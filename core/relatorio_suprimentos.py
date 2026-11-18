"""
============================================================

PRINTER ASSISTANT

RELATÓRIO DE CONFIGURAÇÃO E SUPRIMENTOS

============================================================

Este módulo gera o relatório técnico de configuração,
suprimentos e condição do equipamento.

IMPORTANTE:

Este módulo NÃO realiza nova coleta.

O PrinterDevice já deve estar previamente coletado.

Não chama:

- device.coletar()
- PJL de coleta
- SYSDEBUG
- SNMP
- HTTP

Fluxo:

PrinterDevice
      ↓
extrair_dados()
      ↓
montar_texto()
      ├──────────────→ gerar_pcl() → imprimir()
      │
      └──────────────→ gerar_pdf()

============================================================
"""

import re
import socket

from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PORTA_RAW = 9100

# ------------------------------------------------------------
# Pasta oficial de digitalização.
# ------------------------------------------------------------

PASTA_RELATORIOS = Path(
    r"W:\TEC\Digitalizacao"
)


# ============================================================
# ERRO
# ============================================================

class SuprimentosReportError(Exception):
    """
    Erro controlado do Relatório de Configuração e Suprimentos.
    """

    pass


# ============================================================
# UTILIDADES
# ============================================================

def texto(
    valor,
    padrao="N/D",
):
    if valor is None:
        return padrao

    valor = str(valor).strip()

    if not valor:
        return padrao

    return valor


def numero(
    valor,
    padrao="N/D",
):
    if valor is None:
        return padrao

    try:
        return f"{int(float(valor)):,}".replace(
            ",",
            ".",
        )

    except (
        TypeError,
        ValueError,
    ):
        return texto(
            valor,
            padrao,
        )


def percentual(
    valor,
):
    if valor is None:
        return "N/D"

    try:
        return f"{float(valor):.1f} %"

    except (
        TypeError,
        ValueError,
    ):
        return texto(valor)


def marca(
    valor,
):
    """
    Normaliza uma marca informada manualmente.
    """

    valor = texto(
        valor,
        "",
    )

    if not valor:
        return "NÃO INFORMADA"

    return valor


# ============================================================
# TIPO DE SUPRIMENTO
# ============================================================

def tipo_supply(
    supply,
):
    if not isinstance(
        supply,
        dict,
    ):
        return ""

    tipo = supply.get("tipo")

    if tipo:
        tipo_normalizado = (
            str(tipo)
            .strip()
            .lower()
        )

        if tipo_normalizado in (
            "toner",
            "cartucho",
            "cartridge",
        ):
            return "toner"

        if tipo_normalizado in (
            "unidade_imagem",
            "unidade imagem",
            "unidade de imagem",
            "imaging",
            "imaging unit",
            "photoconductor",
            "fotocondutor",
            "drum",
        ):
            return "unidade_imagem"

        if tipo_normalizado in (
            "fusor",
            "fuser",
            "maintenance",
            "maintenance kit",
            "kit manutenção",
            "kit manutencao",
        ):
            return "fusor"

    nome = (
        supply.get("nome")
        or supply.get("name")
        or supply.get("descricao")
        or supply.get("descrição")
        or supply.get("description")
        or ""
    )

    nome = (
        str(nome)
        .strip()
        .lower()
    )

    if "maintenance kit" in nome:
        return "fusor"

    if (
        "fusor" in nome
        or "fuser" in nome
        or "maintenance" in nome
        or "manuten" in nome
    ):
        return "fusor"

    if (
        "toner" in nome
        or "cartucho" in nome
        or "cartridge" in nome
    ):
        return "toner"

    if (
        "unidade de imagem" in nome
        or "unidade imagem" in nome
        or "imaging unit" in nome
        or "imaging" in nome
        or "photoconductor" in nome
        or "drum" in nome
        or "fotocondutor" in nome
    ):
        return "unidade_imagem"

    return ""


# ============================================================
# LOCALIZAR SUPRIMENTO
# ============================================================

def encontrar_supply(
    supplies,
    tipo,
):
    if not isinstance(
        supplies,
        (list, tuple),
    ):
        return None

    for supply in supplies:

        if not isinstance(
            supply,
            dict,
        ):
            continue

        if tipo_supply(supply) == tipo:
            return supply

    return None


# ============================================================
# STATUS
# ============================================================

def status_supply(
    supply,
):
    if not isinstance(
        supply,
        dict,
    ):
        return "N/D"

    condicao = supply.get(
        "condicao"
    )

    if condicao is None:
        condicao = supply.get(
            "condição"
        )

    if condicao is None:
        return "N/D"

    condicao = str(
        condicao
    ).strip()

    if not condicao:
        return "N/D"

    return condicao


# ============================================================
# EXTRAIR DADOS DO DEVICE
# ============================================================

def extrair_dados(
    device,
):
    """
    Extrai os dados já existentes no PrinterDevice.

    NÃO realiza nova coleta.
    """

    if device is None:
        raise SuprimentosReportError(
            "Nenhuma impressora foi fornecida."
        )

    identificacao = getattr(
        device,
        "identificacao",
        {},
    )

    supplies = getattr(
        device,
        "supplies",
        [],
    )

    ip = getattr(
        device,
        "ip",
        None,
    )

    # --------------------------------------------------------
    # Compatibilidade com to_dict().
    # --------------------------------------------------------

    if (
        not isinstance(
            identificacao,
            dict,
        )
        or not isinstance(
            supplies,
            list,
        )
        or not ip
    ):

        if hasattr(
            device,
            "to_dict",
        ):

            try:
                dados = device.to_dict()

            except Exception as erro:
                raise SuprimentosReportError(
                    "Não foi possível acessar os dados "
                    "do PrinterDevice."
                ) from erro

            if isinstance(
                dados,
                dict,
            ):

                if not isinstance(
                    identificacao,
                    dict,
                ):
                    identificacao = dados.get(
                        "identificacao",
                        dados.get(
                            "identificação",
                            {},
                        ),
                    )

                if not isinstance(
                    supplies,
                    list,
                ):
                    supplies = dados.get(
                        "supplies",
                        [],
                    )

                if not ip:
                    ip = dados.get(
                        "ip"
                    )

    if not isinstance(
        identificacao,
        dict,
    ):
        identificacao = {}

    if not isinstance(
        supplies,
        list,
    ):
        supplies = []

    return (
        identificacao,
        supplies,
        ip,
    )


# ============================================================
# PREPARAR RELATÓRIO
# ============================================================

def preparar_relatorio_configuracao(
    device,
    marca_cartucho=None,
    marca_unidade_imagem=None,
):
    """
    Prepara o conteúdo do Relatório de Configuração
    e Suprimentos.

    Não imprime.
    Não gera PCL.
    Não realiza nova coleta.
    """

    (
        identificacao,
        supplies,
        ip,
    ) = extrair_dados(device)

    texto_relatorio = montar_texto(
        identificacao,
        supplies,
        ip,
        marca_cartucho=marca_cartucho,
        marca_unidade_imagem=marca_unidade_imagem,
    )

    return {
        "sucesso": True,
        "relatório": "configuração",
        "tipo": "configuração_e_suprimentos",
        "texto": texto_relatorio,
        "ip": ip,
        "serial": texto(
            identificacao.get("serial"),
            "SEM_SERIAL",
        ),
        "marca_cartucho": marca(
            marca_cartucho
        ),
        "marca_unidade_imagem": marca(
            marca_unidade_imagem
        ),
    }


# ============================================================
# MONTAR RELATÓRIO
# ============================================================

def montar_texto(
    identificacao,
    supplies,
    ip,
    marca_cartucho=None,
    marca_unidade_imagem=None,
):
    """
    Monta o relatório técnico.

    O layout foi deliberadamente compactado para que
    a impressão física possa caber em UMA página A4,
    mantendo a fonte original segura da impressora.
    """

    fabricante = texto(
        identificacao.get("fabricante"),
        "Lexmark",
    )

    modelo = texto(
        identificacao.get("modelo")
    )

    familia = texto(
        identificacao.get("familia")
    )

    tipo = texto(
        identificacao.get("tipo")
    )

    serial = texto(
        identificacao.get("serial")
    )

    contador = numero(
        identificacao.get("contador")
    )

    firmware = texto(
        identificacao.get("firmware")
    )

    toner = encontrar_supply(
        supplies,
        "toner",
    )

    unidade = encontrar_supply(
        supplies,
        "unidade_imagem",
    )

    fusor = encontrar_supply(
        supplies,
        "fusor",
    )

    marca_cartucho = marca(
        marca_cartucho
    )

    marca_unidade_imagem = marca(
        marca_unidade_imagem
    )

    agora = datetime.now()

    data_relatorio = agora.strftime(
        "%d/%m/%Y %H:%M"
    )

    # ========================================================
    # CABEÇALHO
    # ========================================================

    linhas = [
        "============================================================",
        "                    PRINTER ASSISTANT",
        "          RELATÓRIO DE CONFIGURAÇÃO E SUPRIMENTOS",
        "============================================================",
        f"  DATA: {data_relatorio}    IP: {texto(ip)}",
        "",
        "----------------------- IDENTIFICAÇÃO ----------------------",
        f"  FABRICANTE: {fabricante}    MODELO: {modelo}",
        f"  FAMÍLIA: {familia}    TIPO: {tipo}",
        f"  NÚMERO DE SÉRIE: {serial}",
        f"  CONTADOR: {contador}    FIRMWARE: {firmware}",
        "",
    ]

    # ========================================================
    # TONER
    # ========================================================

    sem_cartucho = any(k in str(marca_cartucho).upper() for k in ("SEM", "NÃO", "AUSENTE"))
    sem_unidade = any(k in str(marca_unidade_imagem).upper() for k in ("SEM", "NÃO", "AUSENTE"))

    linhas.extend(
        [
            "---------------------------- TONER -------------------------",
            (
                f"  MARCA: {marca_cartucho}"
                f"    NÍVEL: N/D"
            ),
        ]
    )

    if sem_cartucho:

        linhas[-1] = (
            "  MARCA: SEM SUPRIMENTO"
            "    NÍVEL: NÃO APLICÁVEL"
            "    CONDIÇÃO: AUSENTE"
        )

        linhas.extend(
            [
                "  STATUS: EQUIPAMENTO EXPEDIDO SEM CARTUCHO DE TONER",
                "  NÚMERO DE SÉRIE: NÃO ACOMPANHA O EQUIPAMENTO",
            ]
        )

    elif toner:

        nivel = toner.get(
            "nivel"
        )

        if nivel is None:
            nivel = toner.get(
                "nível"
            )

        numero_serie = toner.get(
            "numero_serie"
        )

        if numero_serie is None:
            numero_serie = toner.get(
                "número_serie"
            )

        linhas[-1] = (
            f"  MARCA: {marca_cartucho}"
            f"    NÍVEL: {percentual(nivel)}"
            f"    CONDIÇÃO: {status_supply(toner)}"
        )

        linhas.extend(
            [
                (
                    f"  CAPACIDADE: "
                    f"{numero(toner.get('capacidade'))}"
                    f"    RESTANTE: "
                    f"{numero(toner.get('restante'))}"
                    f"    CONSUMIDO: "
                    f"{numero(toner.get('consumido'))}"
                ),
                (
                    f"  NÚMERO DE SÉRIE: "
                    f"{texto(numero_serie)}"
                ),
            ]
        )

    else:

        linhas[-1] = (
            f"  MARCA: {marca_cartucho}"
            f"    NÍVEL: N/D"
            f"    CONDIÇÃO: N/D"
        )

        linhas.extend(
            [
                (
                    "  CAPACIDADE: N/D"
                    "    RESTANTE: N/D"
                    "    CONSUMIDO: N/D"
                ),
                "  NÚMERO DE SÉRIE: N/D",
            ]
        )

    linhas.append("")

    # ========================================================
    # UNIDADE DE IMAGEM
    # ========================================================

    linhas.extend(
        [
            "---------------------- UNIDADE DE IMAGEM ------------------",
            (
                f"  MARCA: {marca_unidade_imagem}"
                f"    NÍVEL: N/D"
            ),
        ]
    )

    if sem_unidade:

        linhas[-1] = (
            "  MARCA: SEM SUPRIMENTO"
            "    NÍVEL: NÃO APLICÁVEL"
            "    CONDIÇÃO: AUSENTE"
        )

        linhas.extend(
            [
                "  STATUS: EQUIPAMENTO EXPEDIDO SEM UNIDADE DE IMAGEM",
                "  NÚMERO DE SÉRIE: NÃO ACOMPANHA O EQUIPAMENTO",
            ]
        )

    elif unidade:

        nivel = unidade.get(
            "nivel"
        )

        if nivel is None:
            nivel = unidade.get(
                "nível"
            )

        numero_serie = unidade.get(
            "numero_serie"
        )

        if numero_serie is None:
            numero_serie = unidade.get(
                "número_serie"
            )

        linhas[-1] = (
            f"  MARCA: {marca_unidade_imagem}"
            f"    NÍVEL: {percentual(nivel)}"
            f"    CONDIÇÃO: {status_supply(unidade)}"
        )

        linhas.extend(
            [
                (
                    f"  CAPACIDADE: "
                    f"{numero(unidade.get('capacidade'))}"
                    f"    RESTANTE: "
                    f"{numero(unidade.get('restante'))}"
                    f"    CONSUMIDO: "
                    f"{numero(unidade.get('consumido'))}"
                ),
                (
                    f"  NÚMERO DE SÉRIE: "
                    f"{texto(numero_serie)}"
                ),
            ]
        )

    else:

        linhas[-1] = (
            f"  MARCA: {marca_unidade_imagem}"
            f"    NÍVEL: N/D"
            f"    CONDIÇÃO: N/D"
        )

        linhas.extend(
            [
                (
                    "  CAPACIDADE: N/D"
                    "    RESTANTE: N/D"
                    "    CONSUMIDO: N/D"
                ),
                "  NÚMERO DE SÉRIE: N/D",
            ]
        )

    linhas.append("")

    # ========================================================
    # FUSOR
    # ========================================================

    linhas.extend(
        [
            "------------------- FUSOR / MANUTENÇÃO --------------------",
        ]
    )

    if fusor:

        nivel = fusor.get(
            "nivel"
        )

        if nivel is None:
            nivel = fusor.get(
                "nível"
            )

        linhas.extend(
            [
                (
                    f"  NÍVEL: {percentual(nivel)}"
                    f"    CONDIÇÃO: {status_supply(fusor)}"
                ),
                (
                    f"  CAPACIDADE: "
                    f"{numero(fusor.get('capacidade'))}"
                    f"    RESTANTE: "
                    f"{numero(fusor.get('restante'))}"
                    f"    CONSUMIDO: "
                    f"{numero(fusor.get('consumido'))}"
                ),
                "  NÚMERO DE SÉRIE: NÃO APLICÁVEL",
            ]
        )

    else:

        linhas.extend(
            [
                "  NÍVEL: N/D    CONDIÇÃO: N/D",
                (
                    "  CAPACIDADE: N/D"
                    "    RESTANTE: N/D"
                    "    CONSUMIDO: N/D"
                ),
                "  NÚMERO DE SÉRIE: NÃO APLICÁVEL",
            ]
        )

    linhas.append("")

    # ========================================================
    # RESUMO
    # ========================================================

    linhas.extend(
        [
            "---------------------------- RESUMO ------------------------",
        ]
    )

    resumo = []

    if sem_cartucho:
        resumo.append(
            "  TONER: NÃO ACOMPANHA (SEM SUPRIMENTO)"
        )
    elif toner:

        nivel = toner.get(
            "nivel"
        )

        if nivel is None:
            nivel = toner.get(
                "nível"
            )

        resumo.append(
            (
                f"  TONER: {percentual(nivel)}"
                f"    {status_supply(toner)}"
            )
        )

    else:
        resumo.append(
            "  TONER: N/D    N/D"
        )

    if sem_unidade:
        resumo.append(
            "  UNIDADE: NÃO ACOMPANHA (SEM SUPRIMENTO)"
        )
    elif unidade:

        nivel = unidade.get(
            "nivel"
        )

        if nivel is None:
            nivel = unidade.get(
                "nível"
            )

        resumo.append(
            (
                f"  UNIDADE: {percentual(nivel)}"
                f"    {status_supply(unidade)}"
            )
        )

    else:
        resumo.append(
            "  UNIDADE: N/D    N/D"
        )

    if fusor:

        nivel = fusor.get(
            "nivel"
        )

        if nivel is None:
            nivel = fusor.get(
                "nível"
            )

        resumo.append(
            (
                f"  FUSOR: {percentual(nivel)}"
                f"    {status_supply(fusor)}"
            )
        )

    else:
        resumo.append(
            "  FUSOR: N/D    N/D"
        )

    linhas.extend(resumo)

    # ========================================================
    # RODAPÉ
    # ========================================================

    linhas.extend(
        [
            "",
            "------------------------------------------------------------",
            "  Relatório gerado pelo Printer Assistant.",
            "  Dados correspondentes ao equipamento no momento",
            "  da coleta realizada pelo sistema.",
            "============================================================",
            "                    FIM DO RELATÓRIO",
            "============================================================",
        ]
    )

    return "\r\n".join(linhas)


# ============================================================
# GERAR PCL
# ============================================================

def gerar_pcl(
    texto_relatorio,
):
    """
    Gera o job PCL enviado para a Lexmark.

    A4 retrato.

    Mantém a configuração física segura que já funcionava:

    - A4
    - retrato
    - 5 LPI
    - fonte de 10 pontos

    O relatório foi compactado horizontalmente para reduzir
    a quantidade de linhas e permitir uma única página física.
    """

    if not texto_relatorio:
        raise SuprimentosReportError(
            "O texto do relatório está vazio."
        )

    dados = b"\x1b%-12345X"

    dados += (
        b'@PJL JOB NAME="PA_RELATORIO_SUPRIMENTOS"\r\n'
    )

    dados += (
        b"@PJL ENTER LANGUAGE=PCL\r\n"
    )

    # Reset PCL
    dados += b"\x1bE"

    # A4
    dados += b"\x1b&l26A"

    # Retrato
    dados += b"\x1b&l0O"

    # Margem esquerda
    dados += b"\x1b&a5L"

    # 5 linhas por polegada
    dados += b"\x1b&l5D"

    # Fonte original segura
    dados += b"\x1b(s0p10h0s0b4099T"

    # PC-850
    dados += b"\x1b(12U"

    texto_limpo = (
        texto_relatorio
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    texto_limpo = texto_limpo.replace(
        "\t",
        "    ",
    )

    linhas = texto_limpo.split("\n")

    for linha in linhas:

        try:
            linha_bytes = linha.encode(
                "cp850"
            )

        except UnicodeEncodeError as erro:

            raise SuprimentosReportError(
                "O relatório contém um caractere "
                "que não pode ser representado pelo "
                "conjunto PC-850 utilizado pelo PCL."
            ) from erro

        dados += linha_bytes
        dados += b"\r\n"

    # Alimentação da página
    dados += b"\x0c"

    # Encerramento PJL
    dados += b"\x1b%-12345X"

    return dados


# ============================================================
# IMPRIMIR
# ============================================================

def imprimir(
    dados,
    ip,
    porta=PORTA_RAW,
):
    """
    Envia o PCL para a impressora.

    O IP vem do PrinterDevice.

    NÃO realiza descoberta.
    NÃO realiza coleta.
    """

    if not ip:
        raise SuprimentosReportError(
            "O endereço IP da impressora "
            "não está disponível."
        )

    if not dados:
        raise SuprimentosReportError(
            "O relatório PCL está vazio."
        )

    try:

        with socket.create_connection(
            (
                ip,
                porta,
            ),
            timeout=10,
        ) as sock:

            sock.sendall(
                dados
            )

    except OSError as erro:

        raise SuprimentosReportError(
            "Não foi possível enviar o relatório "
            f"para {ip}:{porta}.\n\n"
            f"{erro}"
        ) from erro

    return True


# ============================================================
# NOME SEGURO
# ============================================================

def _nome_seguro(
    valor,
    padrao="SEM_SERIAL",
):
    """
    Remove caracteres inválidos para nomes de arquivos
    no Windows.
    """

    valor = texto(
        valor,
        padrao,
    )

    valor = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        valor,
    )

    valor = re.sub(
        r"\s+",
        "_",
        valor,
    )

    valor = valor.strip(
        " ._"
    )

    if not valor:
        valor = padrao

    return valor


# ============================================================
# GERAR PDF
# ============================================================

def _salvar_pdf_nativo_a4(caminho_pdf: Path, texto_relatorio: str):
    """
    Gerador PDF 1.4 nativo (puro Python, sem depender de PyMuPDF/fitz)
    em página única A4 com fonte monoespaçada Courier e WinAnsiEncoding (CP1252).
    """
    largura_pagina = 595
    altura_pagina = 842
    margem_esq = 32
    margem_sup = 28
    margem_inf = 24

    texto_limpo = (
        texto_relatorio
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\t", "    ")
        .replace("•", "*")
    )
    linhas_orig = texto_limpo.split("\n")

    tamanho_fonte = 8.0
    altura_linha = 9.2
    altura_util = altura_pagina - margem_sup - margem_inf

    if len(linhas_orig) * altura_linha > altura_util and len(linhas_orig) > 0:
        altura_linha = max(6.8, altura_util / len(linhas_orig))
        tamanho_fonte = max(6.0, round(altura_linha / 1.15, 1))

    comandos = [
        "BT",
        f"/F1 {tamanho_fonte:.1f} Tf",
        f"{altura_linha:.2f} TL",
        f"{margem_esq} {altura_pagina - margem_sup:.2f} Td",
    ]

    for idx, linha in enumerate(linhas_orig):
        b_cp1252 = linha.encode("cp1252", errors="replace")
        escapado = bytearray()
        for b in b_cp1252:
            if b in (40, 41, 92):
                escapado.append(92)
                escapado.append(b)
            elif 32 <= b <= 126:
                escapado.append(b)
            else:
                escapado.extend(f"\\{b:03o}".encode("ascii"))
        str_pdf = escapado.decode("ascii")
        if idx == 0:
            comandos.append(f"({str_pdf}) Tj")
        else:
            comandos.append(f"T* ({str_pdf}) Tj")

    comandos.append("ET")
    conteudo_stream = "\n".join(comandos).encode("ascii")

    objetos = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {largura_pagina} {altura_pagina}] "
            f"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        ).encode("ascii"),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>\nendobj\n",
        f"5 0 obj\n<< /Length {len(conteudo_stream)} >>\nstream\n".encode("ascii")
        + conteudo_stream
        + b"\nendstream\nendobj\n",
    ]

    pdf_bytes = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objetos:
        offsets.append(len(pdf_bytes))
        pdf_bytes.extend(obj)

    xref_pos = len(pdf_bytes)
    pdf_bytes.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    pdf_bytes.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf_bytes.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf_bytes.extend(
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )

    caminho_pdf.write_bytes(bytes(pdf_bytes))
    return caminho_pdf


def gerar_pdf(
    texto_relatorio,
    modelo,
    serial,
    pasta=None,
):
    """
    Gera a cópia digital em PDF.

    Pasta oficial:

        W:\TEC\Digitalizacao

    Nome:

        MODELO_SERIAL_YYYYMMDD_HHMMSS.pdf

    Exemplo:

        MX611dhe_ABC123456_20260908_163500.pdf

    O PDF possui UMA ÚNICA página A4.
    """

    if not texto_relatorio:
        raise SuprimentosReportError(
            "O texto do relatório está vazio."
        )

    if pasta is None:
        pasta = PASTA_RELATORIOS

    pasta = Path(
        pasta
    )

    try:

        pasta.mkdir(
            parents=True,
            exist_ok=True,
        )

    except OSError as erro:

        raise SuprimentosReportError(
            "Não foi possível acessar ou criar a pasta "
            f"de digitalização:\n{pasta}\n\n"
            "Confirme se a unidade de rede W: está disponível."
        ) from erro

    modelo_seguro = _nome_seguro(
        modelo,
        "SEM_MODELO",
    )

    serial_seguro = _nome_seguro(
        serial,
        "SEM_SERIAL",
    )

    agora = datetime.now()

    timestamp = agora.strftime(
        "%Y%m%d_%H%M%S"
    )

    nome_arquivo = (
        f"{modelo_seguro}_"
        f"{serial_seguro}_"
        f"{timestamp}.pdf"
    )

    caminho_pdf = (
        pasta / nome_arquivo
    )

    try:
        import fitz
    except ImportError:
        try:
            return _salvar_pdf_nativo_a4(caminho_pdf, texto_relatorio)
        except Exception as erro:
            raise SuprimentosReportError(
                f"Não foi possível salvar o PDF do relatório:\n{caminho_pdf}\n\n{erro}"
            ) from erro

    documento = fitz.open()

    try:

        # ----------------------------------------------------
        # A4
        # ----------------------------------------------------

        largura_pagina = 595
        altura_pagina = 842

        margem_esquerda = 32
        margem_direita = 32
        margem_superior = 24
        margem_inferior = 24

        tamanho_fonte = 8

        altura_linha = 9.2

        largura_util = (
            largura_pagina
            - margem_esquerda
            - margem_direita
        )

        fonte = "courier"

        # ----------------------------------------------------
        # Normalização
        # ----------------------------------------------------

        texto_limpo = (
            texto_relatorio
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        texto_limpo = texto_limpo.replace(
            "\t",
            "    ",
        )

        linhas = texto_limpo.split("\n")

        # ----------------------------------------------------
        # Quebra somente se necessário.
        # ----------------------------------------------------

        largura_caractere = (
            tamanho_fonte * 0.60
        )

        caracteres_por_linha = max(
            1,
            int(
                largura_util
                / largura_caractere
            ),
        )

        linhas_pdf = []

        for linha in linhas:

            if not linha:
                linhas_pdf.append("")
                continue

            while len(linha) > caracteres_por_linha:

                linhas_pdf.append(
                    linha[
                        :caracteres_por_linha
                    ]
                )

                linha = linha[
                    caracteres_por_linha:
                ]

            linhas_pdf.append(
                linha
            )

        if not linhas_pdf:
            linhas_pdf = [""]

        # ----------------------------------------------------
        # UMA ÚNICA PÁGINA A4
        # ----------------------------------------------------

        pagina = documento.new_page(
            width=largura_pagina,
            height=altura_pagina,
        )

        area = fitz.Rect(
            margem_esquerda,
            margem_superior,
            largura_pagina - margem_direita,
            altura_pagina - margem_inferior,
        )

        texto_pagina = "\n".join(
            linhas_pdf
        )

        resultado = pagina.insert_textbox(
            area,
            texto_pagina,
            fontsize=tamanho_fonte,
            fontname=fonte,
            lineheight=(
                altura_linha
                / tamanho_fonte
            ),
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT,
        )

        # ----------------------------------------------------
        # Segurança: reduz fonte se necessário.
        # Nunca cria segunda página.
        # ----------------------------------------------------

        if resultado < 0:

            pagina.clean_contents()

            tamanhos_tentativa = (
                7.5,
                7,
                6.5,
            )

            inserido = False

            for tamanho_tentativa in (
                tamanhos_tentativa
            ):

                pagina.clean_contents()

                altura_tentativa = (
                    tamanho_tentativa
                    * 1.15
                )

                resultado = (
                    pagina.insert_textbox(
                        area,
                        texto_pagina,
                        fontsize=tamanho_tentativa,
                        fontname=fonte,
                        lineheight=(
                            altura_tentativa
                            / tamanho_tentativa
                        ),
                        color=(0, 0, 0),
                        align=fitz.TEXT_ALIGN_LEFT,
                    )
                )

                if resultado >= 0:
                    inserido = True
                    break

            if not inserido:

                raise SuprimentosReportError(
                    "O conteúdo do relatório não coube "
                    "em uma única página A4."
                )

        # ----------------------------------------------------
        # Salvar
        # ----------------------------------------------------

        try:

            documento.save(
                str(caminho_pdf),
                garbage=4,
                deflate=True,
            )

        except Exception as erro:

            raise SuprimentosReportError(
                "Não foi possível salvar o PDF "
                f"do relatório:\n{caminho_pdf}"
            ) from erro

    finally:

        documento.close()

    return caminho_pdf


# ============================================================
# DIGITALIZAR
# ============================================================

def digitalizar_relatorio_configuracao(
    device,
    marca_cartucho=None,
    marca_unidade_imagem=None,
):
    """
    Cria a cópia digital em PDF.

    NÃO realiza nova coleta.
    NÃO comunica com a impressora.
    NÃO imprime.
    """

    if device is None:
        raise SuprimentosReportError(
            "Nenhuma impressora foi fornecida."
        )

    if not marca_cartucho:
        raise SuprimentosReportError(
            "A marca do cartucho de toner "
            "não foi informada."
        )

    if not marca_unidade_imagem:
        raise SuprimentosReportError(
            "A marca da unidade de imagem "
            "não foi informada."
        )

    dados = preparar_relatorio_configuracao(
        device,
        marca_cartucho=marca_cartucho,
        marca_unidade_imagem=marca_unidade_imagem,
    )

    identificacao = getattr(
        device,
        "identificacao",
        {},
    )

    modelo = (
        identificacao.get(
            "modelo"
        )
        if isinstance(
            identificacao,
            dict,
        )
        else None
    )

    caminho_pdf = gerar_pdf(
        dados["texto"],
        modelo=modelo,
        serial=dados["serial"],
    )

    return {
        "sucesso": True,
        "relatório": "configuração",
        "tipo": "configuração_e_suprimentos",
        "arquivo": str(caminho_pdf),
        "texto": dados["texto"],
        "ip": dados["ip"],
        "serial": dados["serial"],
        "modelo": texto(
            modelo,
            "SEM_MODELO",
        ),
        "marca_cartucho": marca_cartucho,
        "marca_unidade_imagem": marca_unidade_imagem,
        "mensagem": (
            "Relatório digital gerado com sucesso."
        ),
    }


# ============================================================
# REPORT
# ============================================================

class ReportConfiguracaoSuprimentos:

    title = (
        "Configuração e Suprimentos"
    )

    description = (
        "Relatório técnico de configuração "
        "e suprimentos da impressora."
    )

    category = "Relatórios"

    def generate(
        self,
        session,
        marca_cartucho=None,
        marca_unidade_imagem=None,
    ):
        """
        Gera e imprime o Relatório de Configuração
        e Suprimentos.

        session é o PrinterDevice já coletado.

        NÃO realiza nova coleta.
        """

        dados = preparar_relatorio_configuracao(
            session,
            marca_cartucho=marca_cartucho,
            marca_unidade_imagem=marca_unidade_imagem,
        )

        texto_relatorio = dados[
            "texto"
        ]

        ip = dados[
            "ip"
        ]

        dados_pcl = gerar_pcl(
            texto_relatorio
        )

        imprimir(
            dados_pcl,
            ip,
            PORTA_RAW,
        )

        return {
            "sucesso": True,
            "relatório": "configuração",
            "tipo": "configuração_e_suprimentos",
            "ip": ip,
            "porta": PORTA_RAW,
            "bytes": len(dados_pcl),
            "marca_cartucho": marca(
                marca_cartucho
            ),
            "marca_unidade_imagem": marca(
                marca_unidade_imagem
            ),
            "mensagem": (
                "Relatório de Configuração "
                "e Suprimentos enviado "
                "para a impressora."
            ),
        }


# ============================================================
# COMPATIBILIDADE
# ============================================================

ConfigReport = (
    ReportConfiguracaoSuprimentos
)


# ============================================================
# FUNÇÃO PÚBLICA DE IMPRESSÃO
# ============================================================

def imprimir_relatorio_configuracao(
    device,
    marca_cartucho=None,
    marca_unidade_imagem=None,
):
    """
    Função pública utilizada pela interface/ReportService.

    Recebe o PrinterDevice e as marcas informadas
    manualmente.

    NÃO realiza nova coleta.
    """

    if device is None:
        raise SuprimentosReportError(
            "Nenhuma impressora foi fornecida."
        )

    if not marca_cartucho:
        raise SuprimentosReportError(
            "A marca do cartucho de toner "
            "não foi informada."
        )

    if not marca_unidade_imagem:
        raise SuprimentosReportError(
            "A marca da unidade de imagem "
            "não foi informada."
        )

    relatorio = (
        ReportConfiguracaoSuprimentos()
    )

    return relatorio.generate(
        device,
        marca_cartucho=marca_cartucho,
        marca_unidade_imagem=marca_unidade_imagem,
    )


# ============================================================
# FIM DO RELATÓRIO
# ============================================================