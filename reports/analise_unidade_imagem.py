"""
============================================================
PRINTER ASSISTANT
LAUDO TÉCNICO PERICIAL — ANÁLISE CRÍTICA DA UNIDADE DE IMAGEM
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


def _calcular_idade_meses(data_instalacao_str):
    if not data_instalacao_str or data_instalacao_str == "N/D":
        return None
    try:
        match_iso = re.search(r'(\d{4})[-/]?(\d{2})[-/]?(\d{2})', str(data_instalacao_str))
        if match_iso:
            d = datetime(int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3)))
        else:
            match_br = re.search(r'(\d{2})[-/]?(\d{2})[-/]?(\d{4})', str(data_instalacao_str))
            if match_br:
                d = datetime(int(match_br.group(3)), int(match_br.group(2)), int(match_br.group(1)))
            else:
                return None
        dias = (datetime.now() - d).days
        return max(0, round(dias / 30.4))
    except Exception:
        return None


def _avaliar_garantia_completa(data_instalacao_str, nivel_restante_num, meses_idade):
    """
    Avalia as regras de garantia técnica:
    - Idade de instalação <= 12 meses (365 dias).
    - Desgaste: Vida útil restante >= 50% (consumo <= 50%).
    """
    if not data_instalacao_str or data_instalacao_str == "N/D":
        return {
            "icone": "?",
            "status": "NÃO CONCLUÍDO (Data de instalação não identificada)",
            "idade_status": "Pendente de validação da data",
            "nivel_status": "Aprovado" if (nivel_restante_num is not None and nivel_restante_num >= 50) else "Reprovado",
            "conclusao": "Não foi possível validar a data de instalação para atestar a garantia."
        }

    idade_valida = (meses_idade is not None and meses_idade <= 12)
    nivel_valido = (nivel_restante_num is not None and nivel_restante_num >= 50.0)

    if idade_valida and nivel_valido:
        return {
            "icone": "✔",
            "status": "ELEGÍVEL PARA GARANTIA (EM GARANTIA)",
            "idade_status": f"Aprovado (~{meses_idade} meses <= limite de 12 meses)",
            "nivel_status": f"Aprovado ({nivel_restante_num:.0f}% restante >= mínimo de 50%)",
            "conclusao": "A peça cumpre integralmente os requisitos operacionais para cobertura ou troca em garantia (RMA)."
        }
    elif not idade_valida and not nivel_valido:
        return {
            "icone": "✖",
            "status": "NÃO ELEGÍVEL (Tempo e desgaste excedidos)",
            "idade_status": f"Reprovado (~{meses_idade} meses > limite de 12 meses)",
            "nivel_status": f"Reprovado ({nivel_restante_num:.0f}% restante < 50%)",
            "conclusao": "Prazo de 12 meses expirado e limite máximo de desgaste de 50% ultrapassado."
        }
    elif not idade_valida:
        return {
            "icone": "✖",
            "status": "NÃO ELEGÍVEL (Tempo de instalação expirado)",
            "idade_status": f"Reprovado (~{meses_idade} meses > limite de 12 meses)",
            "nivel_status": f"Aprovado ({nivel_restante_num:.0f}% restante >= 50%)",
            "conclusao": "Prazo limite de garantia de 12 meses excedido desde a data de registro do componente."
        }
    else:
        return {
            "icone": "✖",
            "status": "NÃO ELEGÍVEL (Desgaste superior a 50%)",
            "idade_status": f"Aprovado (~{meses_idade} meses <= limite de 12 meses)",
            "nivel_status": f"Reprovado ({nivel_restante_num:.0f}% restante < 50%)",
            "conclusao": "Desgaste natural excessivo superior a 50% da vida útil do fotocondutor."
        }


def extrair_dados_unidade(device):
    """
    Extrai do sysdebug_filtered e device os dados técnicos e métricas da Unidade de Imagem.
    """
    if device is None:
        raise AnaliseUnidadeError("Nenhum equipamento foi fornecido.")

    dados_dev = device.to_dict() if hasattr(device, "to_dict") else {}
    identificacao = dados_dev.get("identificacao", {}) or {}

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

    part_number = _primeiro_definido(
        sysdebug_filtered.get("drum_part_number"),
        supply_unidade.get("part_number"),
        padrao="50F0Z00",
    )

    chip_id = _primeiro_definido(sysdebug_filtered.get("drum_chip_id"), padrao="N/D")
    chip_ec = _primeiro_definido(sysdebug_filtered.get("drum_chip_ec_level"), padrao="N/D")

    # Páginas e contadores
    paginas_raw = _primeiro_definido(
        sysdebug_filtered.get("drum_page_count"),
        sysdebug_filtered.get("photoconductor_page_count"),
        sysdebug_filtered.get("imaging_pages_printed"),
        supply_unidade.get("consumido"),
        padrao=0,
    )
    try:
        paginas_num = int(float(paginas_raw))
    except (ValueError, TypeError):
        paginas_num = 0

    rotacoes_raw = _primeiro_definido(
        sysdebug_filtered.get("drum_rotations"),
        sysdebug_filtered.get("pc_rotations"),
        supply_unidade.get("rotacoes"),
        padrao=0,
    )
    try:
        rotacoes_num = int(float(rotacoes_raw))
    except (ValueError, TypeError):
        rotacoes_num = 0

    cap_raw = _primeiro_definido(
        sysdebug_filtered.get("drum_max_capacity"),
        supply_unidade.get("capacidade"),
        padrao=60000,
    )
    try:
        capacidade_num = int(float(cap_raw))
    except (ValueError, TypeError):
        capacidade_num = 60000

    nivel_raw = _primeiro_definido(
        sysdebug_filtered.get("drum_life_remaining"),
        supply_unidade.get("nivel"),
        supply_unidade.get("percentual"),
        padrao=100,
    )
    try:
        nivel_num = float(nivel_raw)
    except (ValueError, TypeError):
        nivel_num = 100.0

    rem_raw = _primeiro_definido(
        sysdebug_filtered.get("drum_pages_remaining"),
        supply_unidade.get("restante"),
        padrao=max(0, capacidade_num - paginas_num),
    )
    try:
        paginas_restantes_num = int(float(rem_raw))
    except (ValueError, TypeError):
        paginas_restantes_num = max(0, capacidade_num - paginas_num)

    instalacao_drum = _primeiro_definido(
        sysdebug_filtered.get("drum_install_date"),
        sysdebug_filtered.get("pc_install_date"),
        _decodificar_data_serial(serial_drum),
        padrao="N/D",
    )

    meses_idade = _calcular_idade_meses(instalacao_drum)
    garantia_info = _avaliar_garantia_completa(instalacao_drum, nivel_num, meses_idade)

    # Métricas avançadas de limpeza e motor
    ttc = _primeiro_definido(sysdebug_filtered.get("drum_toner_to_cleaner"), padrao="N/D")
    developer = _primeiro_definido(sysdebug_filtered.get("drum_filtered_toner_dvlpr"), padrao="N/D")
    sides_por = _primeiro_definido(sysdebug_filtered.get("pc_sides_since_por"), padrao=0)
    rotations_por = _primeiro_definido(sysdebug_filtered.get("pc_rotations_since_por"), padrao=0)

    condicao_mec = "EXCELENTE (Dentro dos padrões operacionais)"
    if nivel_num < 20.0 or (paginas_num > 0 and (rotacoes_num / paginas_num) > 30):
        condicao_mec = "ATENÇÃO (Desgaste elevado ou alto índice de rotações)"

    return {
        "modelo": identificacao.get("modelo") or (getattr(device, "modelo", "")() if callable(getattr(device, "modelo", None)) else getattr(device, "modelo", "")) or "Não identificado",
        "serial_impressora": identificacao.get("serial") or getattr(device, "serial", "N/D"),
        "ip": dados_dev.get("ip") or getattr(device, "ip", "N/D"),
        "firmware": identificacao.get("firmware") or getattr(device, "firmware", "Desconhecido"),
        "paginas_impressora": _formatar_numero(identificacao.get("contador")),
        "serial_drum": serial_drum,
        "part_number": part_number,
        "chip_id": chip_id,
        "chip_ec": chip_ec,
        "paginas_drum": _formatar_numero(paginas_num),
        "paginas_num": paginas_num,
        "capacidade_num": capacidade_num,
        "paginas_restantes": _formatar_numero(paginas_restantes_num),
        "nivel_drum": f"{nivel_num:.0f}%",
        "nivel_num": nivel_num,
        "rotacoes_drum": _formatar_numero(rotacoes_num),
        "rotacoes_num": rotacoes_num,
        "instalacao_drum": instalacao_drum,
        "idade_meses": meses_idade,
        "ttc": _formatar_numero(ttc),
        "developer": _formatar_numero(developer),
        "sides_por": _formatar_numero(sides_por),
        "rotations_por": _formatar_numero(rotations_por),
        "condicao_mecanica": condicao_mec,
        "garantia_icone": garantia_info["icone"],
        "status_garantia": garantia_info["status"],
        "garantia_idade_status": garantia_info["idade_status"],
        "garantia_nivel_status": garantia_info["nivel_status"],
        "garantia_conclusao": garantia_info["conclusao"],
    }


def montar_texto_analise(dados_unidade):
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    cap = dados_unidade.get("capacidade_num") or 60000
    pg_num = dados_unidade.get("paginas_num") or 0
    rot_num = dados_unidade.get("rotacoes_num") or 0

    pct_consumo = f"{(pg_num / cap) * 100:.1f}%".replace('.', ',') if cap > 0 else "N/D"
    media_ciclos = f"{(rot_num / pg_num):.2f} ciclos por página impressa".replace('.', ',') if (rot_num and pg_num and pg_num > 0) else "N/D"

    idade_meses = dados_unidade.get("idade_meses")
    idade_txt = f"~{idade_meses} meses" if idade_meses is not None else "Data não identificada"

    linhas = [
        "================================================================================",
        "                            PRINTER ASSISTANT                            ",
        "               LAUDO TÉCNICO PERICIAL — UNIDADE DE IMAGEM               ",
        "================================================================================",
        f" Data da Emissão: {agora:<30} Endereço IP: {dados_unidade['ip']}",
        f" Responsável: Bancada Técnica / Laboratório     Equipamento: {dados_unidade['modelo']}",
        "================================================================================",
        "",
        "1. IDENTIFICAÇÃO DO EQUIPAMENTO E CHASSI",
        "--------------------------------------------------------------------------------",
        f" • Modelo da Impressora:       {dados_unidade['modelo']}",
        f" • Número de Série (Chassi):   {dados_unidade['serial_impressora']}",
        f" • Hodômetro Geral (Máquina):  {dados_unidade['paginas_impressora']} páginas impressas",
        f" • Versão de Firmware:         {dados_unidade['firmware']}",
        "",
        "2. FICHA TÉCNICA DO CILINDRO FOTOCONDUTOR (DRUM)",
        "--------------------------------------------------------------------------------",
        f" • Part Number (Código Peça):  {dados_unidade['part_number']} (Unidade de Imagem 60K)",
        f" • Número de Série do Chip:    {dados_unidade['serial_drum']}",
        f" • ID do Chip / Revisão:       {dados_unidade['chip_id']} (EC Level {dados_unidade['chip_ec']})",
        f" • Data de Instalação/Chip:    {dados_unidade['instalacao_drum']} ({idade_txt})",
        "",
        "3. HISTÓRICO DE CONSUMO E DESGASTE MECÂNICO",
        "--------------------------------------------------------------------------------",
        f" • Capacidade Nominal:         {_formatar_numero(cap)} páginas",
        f" • Páginas Impressas no Drum:  {dados_unidade['paginas_drum']} páginas ({pct_consumo} de consumo)",
        f" • Vida Útil Restante (Chip):  {dados_unidade['nivel_drum']} (~{dados_unidade['paginas_restantes']} páginas estimadas)",
        f" • Ciclos Totais do Tambor:    {dados_unidade['rotacoes_drum']} rotações acumuladas",
        f" • Média de Rotações / Página: {media_ciclos}",
        f" • Atividade no Ciclo Atual:   {dados_unidade['sides_por']} páginas / {dados_unidade['rotations_por']} rotações desde o último reinício",
        "",
        "4. AVALIAÇÃO DE ESTADO E FLUIDEZ DO SISTEMA",
        "--------------------------------------------------------------------------------",
        f" • Resíduo na Limpeza (TTC):   {dados_unidade['ttc']} contagens (Descarte de toner limpo)",
        f" • Filtro de Toner Revelador:  {dados_unidade['developer']} partículas registradas",
        f" • Condição Mecânica Geral:    {dados_unidade['condicao_mecanica']}",
        "",
        "5. PARECER TÉCNICO DE GARANTIA (RMA)",
        "--------------------------------------------------------------------------------",
        f" [ {dados_unidade['garantia_icone']} ] STATUS: {dados_unidade['status_garantia']}",
        "",
        " Justificativa Técnica:",
        f"  1. Idade do Componente: Instalado/registrado em {dados_unidade['instalacao_drum']} ({idade_txt}).",
        f"     Critério de garantia: Idade máxima de 12 meses ({dados_unidade['garantia_idade_status']}).",
        f"  2. Nível de Desgaste:   Consumido {pct_consumo} / Restante {dados_unidade['nivel_drum']}.",
        f"     Critério de garantia: Nível restante deve ser >= 50% ({dados_unidade['garantia_nivel_status']}).",
        "",
        f" Conclusão: {dados_unidade['garantia_conclusao']}",
        "",
        "================================================================================",
        " Relatório de Análise Crítica gerado via Printer Assistant.",
        "================================================================================",
    ]
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

    # Tenta salvar prioritariamente em W:\TEC\Digitalizacao; se W: não existir, salva local
    pasta = Path(r"W:\TEC\Digitalizacao")
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except Exception:
        pasta = Path("relatorios_digitalizados")
        pasta.mkdir(parents=True, exist_ok=True)

    nome_arquivo = f"ANALISE_DRUM_{dados_unidade['serial_drum']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    caminho = pasta / nome_arquivo

    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_textbox(fitz.Rect(30, 30, 565, 810), texto, fontsize=8, fontname="courier")
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
