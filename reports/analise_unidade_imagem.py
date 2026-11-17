"""
============================================================
PRINTER ASSISTANT
RELATÓRIO DE ANÁLISE DE UNIDADE DE IMAGEM (VIA SYSDEBUG_FILTERED)
============================================================
"""

from datetime import datetime, timedelta
import socket
import re
from pathlib import Path


class AnaliseUnidadeError(Exception):
    """Erro controlado da Análise da Unidade de Imagem."""
    pass


def _primeiro_definido(*valores, padrao="N/D"):
    for v in valores:
        if v is not None and str(v).strip() not in ("", "None", "N/D", "Desconhecido"):
            return v
    return padrao


def _decodificar_data_serial(serial):
    if not serial or str(serial).strip() in ("", "N/D", "Desconhecido"):
        return None
    m = re.match(r"^[A-Z]{3}(\d{2})(\d{3})", str(serial).strip().upper())
    if not m:
        return None
    try:
        yy = int(m.group(1))
        ddd = int(m.group(2))
        ano = 2000 + yy
        if 2000 <= ano <= 2099 and 1 <= ddd <= 366:
            dt = datetime(ano, 1, 1) + timedelta(days=ddd - 1)
            return dt.strftime("%d/%m/%Y")
    except Exception:
        pass
    return None


def _formatar_numero(valor, padrao="N/D"):
    if valor is None:
        return padrao
    try:
        return f"{int(float(valor)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(valor) if str(valor).strip() else padrao


def _avaliar_garantia(data_instalacao_str, nivel_restante_str):
    """
    Avalia as regras de garantia:
    - Máximo de 12 meses (365 dias) desde a data de instalação.
    - Máximo de 50% de uso (Vida útil restante deve ser >= 50%).
    """
    if not data_instalacao_str or data_instalacao_str == "N/D":
        return "N/D (Falta data de instalação)"
    
    if not nivel_restante_str or nivel_restante_str == "N/D":
        return "N/D (Falta nível de vida útil)"

    # 1. Avaliar Nível (Requer >= 50% restante)
    nivel_valido = False
    nivel_detectado = 0
    try:
        numeros = re.findall(r'\d+', str(nivel_restante_str))
        if numeros:
            nivel_detectado = float(numeros[0])
            if nivel_detectado >= 50.0:
                nivel_valido = True
    except Exception:
        return "N/D (Erro ao ler nível)"

    # 2. Avaliar Data (Requer <= 365 dias)
    data_valida = False
    try:
        hoje = datetime.now()
        data_inst = None
        
        match_iso = re.search(r'(\d{4})[-/]?(\d{2})[-/]?(\d{2})', str(data_instalacao_str))
        if match_iso:
            ano, mes, dia = int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3))
            if ano > 1900:
                data_inst = datetime(ano, mes, dia)
        
        if not data_inst:
            match_br = re.search(r'(\d{2})[-/]?(\d{2})[-/]?(\d{4})', str(data_instalacao_str))
            if match_br:
                dia, mes, ano = int(match_br.group(1)), int(match_br.group(2)), int(match_br.group(3))
                data_inst = datetime(ano, mes, dia)

        if data_inst:
            if (hoje - data_inst).days <= 365:
                data_valida = True
        else:
            return "N/D (Formato de data desconhecido)"
            
    except Exception:
        return "N/D (Erro ao processar data)"

    # 3. Veredito da Garantia
    if nivel_valido and data_valida:
        return "EM GARANTIA (Instalado há menos de 12 meses E uso em até 50%)"
    elif not nivel_valido and not data_valida:
        return f"FORA DE GARANTIA (Instalação > 12 meses E uso > 50%. Resta: {nivel_detectado}%)"
    elif not nivel_valido:
        return f"FORA DE GARANTIA (Uso superior a 50%. Resta: {nivel_detectado}%)"
    elif not data_valida:
        return "FORA DE GARANTIA (Instalação superior a 12 meses)"


def extrair_dados_unidade(device):
    """
    Extrai do sysdebug_filtered os dados EXCLUSIVOS da Unidade de Imagem.
    """
    if device is None:
        raise AnaliseUnidadeError("Nenhum equipamento foi fornecido.")

    dados_dev = device.to_dict() if hasattr(device, "to_dict") else {}
    identificacao = dados_dev.get("identificacao", {}) or {}
    
    # Busca estrita do sysdebug_filtered
    sysdebug_filtered = getattr(device, "sysdebug_filtered", None)
    if not sysdebug_filtered and isinstance(dados_dev, dict):
        sysdebug_filtered = dados_dev.get("sysdebug_filtered", {})
    if not sysdebug_filtered and isinstance(dados_dev, dict):
        raw_sys = dados_dev.get("raw_sysdebug") or getattr(device, "raw_sysdebug", {})
        if isinstance(raw_sys, dict) and isinstance(raw_sys.get("sysdebug_filtered"), dict):
            sysdebug_filtered = raw_sys.get("sysdebug_filtered", {})

    if not isinstance(sysdebug_filtered, dict):
        sysdebug_filtered = {}

    supplies = dados_dev.get("supplies", []) or []
    supply_unidade = {}
    for item in supplies:
        tipo = str(item.get("tipo", "")).lower()
        nome = str(item.get("nome", "") or item.get("descricao", "")).lower()
        if "unidade" in tipo or "imagem" in tipo or "drum" in tipo or "photoconductor" in tipo or \
           "unidade" in nome or "imagem" in nome or "drum" in nome or "fotocondutor" in nome:
            supply_unidade = item
            break

    serial_drum = _primeiro_definido(
        sysdebug_filtered.get("drum_serial"),
        sysdebug_filtered.get("photoconductor_serial"),
        sysdebug_filtered.get("imaging_unit_serial"),
        supply_unidade.get("numero_serie"),
        supply_unidade.get("serial"),
        padrao="N/D",
    )

    paginas_drum = _primeiro_definido(
        sysdebug_filtered.get("drum_page_count"),
        sysdebug_filtered.get("photoconductor_page_count"),
        sysdebug_filtered.get("imaging_pages_printed"),
        sysdebug_filtered.get("pc_pages"),
        supply_unidade.get("consumido"),
        padrao="N/D",
    )

    nivel_drum = _primeiro_definido(
        sysdebug_filtered.get("drum_life_remaining"),
        sysdebug_filtered.get("photoconductor_ok"),
        supply_unidade.get("nivel"),
        supply_unidade.get("percentual"),
        padrao="N/D",
    )

    rotacoes_drum = _primeiro_definido(
        sysdebug_filtered.get("drum_rotations"),
        sysdebug_filtered.get("pc_rotations"),
        padrao="N/D",
    )

    instalacao_drum = _primeiro_definido(
        sysdebug_filtered.get("drum_install_date"),
        sysdebug_filtered.get("pc_install_date"),
        _decodificar_data_serial(serial_drum),
        padrao="N/D",
    )

    status_garantia = _avaliar_garantia(instalacao_drum, nivel_drum)

    return {
        "modelo": identificacao.get("modelo", getattr(device, "modelo", "Lexmark")),
        "serial_impressora": identificacao.get("serial", getattr(device, "serial", "N/D")),
        "ip": dados_dev.get("ip") or getattr(device, "ip", "N/D"),
        "serial_drum": serial_drum,
        "paginas_drum": _formatar_numero(paginas_drum),
        "paginas_impressora": _formatar_numero(identificacao.get("contador")),
        "nivel_drum": f"{float(nivel_drum):.0f}%" if str(nivel_drum).replace('.', '', 1).isdigit() else str(nivel_drum),
        "rotacoes_drum": _formatar_numero(rotacoes_drum),
        "instalacao_drum": instalacao_drum,
        "status_garantia": status_garantia,
        "sysdebug_raw": sysdebug_filtered
    }


def montar_texto_analise(dados_unidade):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    linhas = [
        "============================================================",
        "                    PRINTER ASSISTANT                       ",
        "            ANÁLISE TÉCNICA DA UNIDADE DE IMAGEM            ",
        "============================================================",
        f" DATA: {agora}     IP: {dados_unidade['ip']}",
        "",
        "------------------ IDENTIFICAÇÃO DO EQUIPAMENTO -------------",
        f" MODELO IMPRESSORA: {dados_unidade['modelo']}",
        f" SERIAL IMPRESSORA: {dados_unidade['serial_impressora']}",
        f" CONTADOR DA IMPRESSORA: {dados_unidade['paginas_impressora']} pág.",
        "",
        "------------------ MÉTRICAS DA UNIDADE DE IMAGEM ------------",
        f" NÚMERO DE SÉRIE (CILINDRO): {dados_unidade['serial_drum']}",
        f" PÁGINAS PROCESSADAS (DRUM): {dados_unidade['paginas_drum']} pág.",
        f" VIDA ÚTIL RESTANTE:         {dados_unidade['nivel_drum']}",
        f" CICLOS / ROTAÇÕES:          {dados_unidade['rotacoes_drum']}",
        f" DATA DE INSTALAÇÃO:         {dados_unidade['instalacao_drum']}",
        "",
        "------------------ DIAGNÓSTICO DE GARANTIA ------------------",
        f" STATUS: {dados_unidade['status_garantia']}",
        " Regra: Máximo de 12 meses da data de instalação E máximo",
        " de 50% de uso (Vida útil restante >= 50%).",
        "",
        "------------------ DIAGNÓSTICO SYSDEBUG_FILTERED ------------",
    ]

    sysdebug_f = dados_unidade.get("sysdebug_raw", {})
    if isinstance(sysdebug_f, dict) and sysdebug_f:
        for k, v in sysdebug_f.items():
            if "drum" in k.lower() or "pc_" in k.lower() or "imaging" in k.lower():
                linhas.append(f"  • {k}: {v}")
    else:
        linhas.append("  • Nenhuma chave crítica específica detectada em sysdebug_filtered.")

    linhas.extend([
        "",
        "============================================================",
        " Relatório técnico gerado via Sysdebug Filtered.",
        "============================================================",
    ])

    return "\r\n".join(linhas)


def preparar_analise_unidade(device):
    dados = extrair_dados_unidade(device)
    texto = montar_texto_analise(dados)
    return {"texto": texto, "dados": dados}


def imprimir_analise_unidade(device):
    dados_unidade = extrair_dados_unidade(device)
    texto = montar_texto_analise(dados_unidade)
    ip = dados_unidade["ip"]

    if not ip or ip == "N/D":
        raise AnaliseUnidadeError("IP da impressora não encontrado.")

    pcl = (
        b"\x1b%-12345X"
        b'@PJL JOB NAME="PA_ANALISE_DRUM"\r\n'
        b"@PJL ENTER LANGUAGE=PCL\r\n"
        b"\x1bE"
        b"\x1b&l26A"
        b"\x1b&l0O"
        b"\x1b(s0p10h0s0b4099T"
        + texto.encode("cp850", errors="replace") +
        b"\x0c\x1b%-12345X"
    )

    try:
        with socket.create_connection((ip, 9100), timeout=10) as sock:
            sock.sendall(pcl)
        return True
    except Exception as e:
        raise AnaliseUnidadeError(f"Falha ao enviar impressão para {ip}:9100.\n{e}")


def digitalizar_analise_unidade(device):
    dados_unidade = extrair_dados_unidade(device)
    texto = montar_texto_analise(dados_unidade)
    
    pasta = Path(r"W:\TEC\Digitalizacao")
    pasta.mkdir(parents=True, exist_ok=True)
    
    nome_arquivo = f"ANALISE_DRUM_{dados_unidade['serial_drum']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = pasta / nome_arquivo

    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_textbox(fitz.Rect(35, 35, 560, 800), texto, fontsize=9, fontname="courier")
        doc.save(str(caminho))
        doc.close()
        return {"arquivo": str(caminho)}
    except ImportError:
        try:
            from core.relatorio_suprimentos import _salvar_pdf_nativo_a4
            _salvar_pdf_nativo_a4(caminho, texto)
            return {"arquivo": str(caminho)}
        except Exception as e:
            raise AnaliseUnidadeError(f"Erro ao gerar PDF: {e}")
    except Exception as e:
        raise AnaliseUnidadeError(f"Erro ao gerar PDF: {e}")