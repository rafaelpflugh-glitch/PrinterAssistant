import asyncio
import re
import socket
from datetime import datetime

from core.device import PrinterDevice
from core.pjl import PJLPrinter


# ============================================================
# PRINTER ASSISTANT
# RELATORIO DE CONFIGURACAO E SUPRIMENTOS
#
# IMPORTANTE:
# A ROTINA DE COLETA NAO FOI ALTERADA.
#
# PJL + SYSDEBUG + SNMP
#
# ALTERACAO DESTA VERSAO:
# SOMENTE O TAMANHO DOS TITULOS.
#
# TODOS OS TITULOS AGORA USAM O MESMO TAMANHO DO CORPO.
# ============================================================


IP_IMPRESSORA = "192.168.14.134"
PORTA_RAW = 9100


# ============================================================
# UTILIDADES
# ============================================================

def texto(valor, padrao="N/D"):

    if valor is None:
        return padrao

    valor = str(valor).strip()

    if not valor:
        return padrao

    return valor


def numero(valor, padrao="N/D"):

    if valor is None:
        return padrao

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):

        return texto(
            valor,
            padrao
        )


def percentual(valor):

    if valor is None:
        return "N/D"

    try:

        return f"{float(valor):.1f} %"

    except (TypeError, ValueError):

        return texto(valor)


def encontrar_supply(
    supplies,
    tipo
):

    for supply in supplies:

        if not isinstance(
            supply,
            dict
        ):
            continue

        supply_tipo = str(
            supply.get("tipo") or ""
        ).strip().lower()

        if supply_tipo == tipo:

            return supply

    return None


# ============================================================
# FIRMWARE
# ============================================================

def extrair_firmware(
    info_config
):

    if not info_config:
        return None

    padrao = re.search(
        r"(?im)^\s*SYSTEM\s+FIRMWARE\s+VERSION\s*=\s*(.+?)\s*$",
        info_config
    )

    if not padrao:
        return None

    return padrao.group(1).strip()


# ============================================================
# MONTAR RELATORIO
# ============================================================

def montar_texto(
    identificacao,
    supplies,
    firmware
):

    fabricante = texto(
        identificacao.get(
            "fabricante"
        ),
        "Lexmark"
    )

    modelo = texto(
        identificacao.get(
            "modelo"
        )
    )

    serial = texto(
        identificacao.get(
            "serial"
        )
    )

    contador = numero(
        identificacao.get(
            "contador"
        )
    )

    toner = encontrar_supply(
        supplies,
        "toner"
    )

    unidade = encontrar_supply(
        supplies,
        "unidade_imagem"
    )

    fusor = encontrar_supply(
        supplies,
        "fusor"
    )

    agora = datetime.now()

    data_relatorio = agora.strftime(
        "%d/%m/%Y %H:%M"
    )

    linhas = []

    # ========================================================
    # CABECALHO
    # ========================================================

    linhas.append("")

    linhas.append(
        "                 PRINTER ASSISTANT"
    )

    linhas.append(
        "          RELATORIO TECNICO DE EQUIPAMENTO"
    )

    linhas.append(
        "             CONFIGURACAO E SUPRIMENTOS"
    )

    linhas.append("")

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append(
        f"  DATA DO RELATORIO: {data_relatorio}"
    )

    linhas.append(
        f"  IP DO EQUIPAMENTO: {IP_IMPRESSORA}"
    )

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append("")

    # ========================================================
    # IMPRESSORA
    # ========================================================

    linhas.append(
        "                    IMPRESSORA"
    )

    linhas.append(
        "============================================================"
    )

    linhas.append(
        f"  FABRICANTE     : {fabricante}"
    )

    linhas.append(
        f"  MODELO         : {modelo}"
    )

    linhas.append(
        f"  NUMERO DE SERIE: {serial}"
    )

    linhas.append(
        f"  CONTADOR       : {contador}"
    )

    linhas.append(
        f"  FIRMWARE       : {texto(firmware)}"
    )

    linhas.append(
        "============================================================"
    )

    linhas.append("")

    # ========================================================
    # CARTUCHO
    # ========================================================

    linhas.append(
        "                       CARTUCHO"
    )

    linhas.append(
        "------------------------------------------------------------"
    )

    if toner:

        linhas.append(
            "  FABRICANTE     : N/D"
        )

        linhas.append(
            f"  NIVEL          : "
            f"{percentual(toner.get('nivel'))}"
        )

        linhas.append(
            f"  CAPACIDADE     : "
            f"{numero(toner.get('capacidade'))}"
        )

        linhas.append(
            f"  NUMERO DE SERIE: "
            f"{texto(toner.get('numero_serie'))}"
        )

    else:

        linhas.append(
            "  FABRICANTE     : N/D"
        )

        linhas.append(
            "  NIVEL          : N/D"
        )

        linhas.append(
            "  CAPACIDADE     : N/D"
        )

        linhas.append(
            "  NUMERO DE SERIE: N/D"
        )

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append("")

    # ========================================================
    # UNIDADE DE IMAGEM
    # ========================================================

    linhas.append(
        "                  UNIDADE DE IMAGEM"
    )

    linhas.append(
        "------------------------------------------------------------"
    )

    if unidade:

        linhas.append(
            "  FABRICANTE     : N/D"
        )

        linhas.append(
            f"  NIVEL          : "
            f"{percentual(unidade.get('nivel'))}"
        )

        linhas.append(
            f"  CAPACIDADE     : "
            f"{numero(unidade.get('capacidade'))}"
        )

        linhas.append(
            f"  NUMERO DE SERIE: "
            f"{texto(unidade.get('numero_serie'))}"
        )

    else:

        linhas.append(
            "  FABRICANTE     : N/D"
        )

        linhas.append(
            "  NIVEL          : N/D"
        )

        linhas.append(
            "  CAPACIDADE     : N/D"
        )

        linhas.append(
            "  NUMERO DE SERIE: N/D"
        )

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append("")

    # ========================================================
    # FUSOR
    # ========================================================

    linhas.append(
        "                 KIT DE MANUTENCAO / FUSOR"
    )

    linhas.append(
        "------------------------------------------------------------"
    )

    if fusor:

        linhas.append(
            f"  NIVEL          : "
            f"{percentual(fusor.get('nivel'))}"
        )

        linhas.append(
            f"  CAPACIDADE     : "
            f"{numero(fusor.get('capacidade'))}"
        )

        linhas.append(
            "  NUMERO DE SERIE: NAO APLICAVEL"
        )

    else:

        linhas.append(
            "  NIVEL          : N/D"
        )

        linhas.append(
            "  CAPACIDADE     : N/D"
        )

        linhas.append(
            "  NUMERO DE SERIE: NAO APLICAVEL"
        )

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append("")

    # ========================================================
    # OBSERVACOES
    # ========================================================

    linhas.append(
        "                    OBSERVACOES"
    )

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append(
        "  Relatorio gerado automaticamente pelo Printer Assistant."
    )

    linhas.append(
        "  Os dados de identificacao e suprimentos foram obtidos"
    )

    linhas.append(
        "  atraves das interfaces disponiveis do equipamento."
    )

    linhas.append(
        "------------------------------------------------------------"
    )

    linhas.append("")

    linhas.append(
        "                 FIM DO RELATORIO"
    )

    linhas.append("")

    return "\r\n".join(linhas)


# ============================================================
# GERAR PCL
#
# IMPORTANTE:
#
# TODOS OS TEXTOS USAM A MESMA FONTE.
#
# NAO EXISTE MAIS FONTE ESPECIAL PARA TITULOS.
#
# CORPO:
# Courier 10 pt
#
# Assim eliminamos a diferenca visual de tamanho.
# ============================================================

def gerar_pcl(
    texto_relatorio
):

    dados = b"\x1b%-12345X"

    # ========================================================
    # JOB PJL
    # ========================================================

    dados += (
        b'@PJL JOB NAME="PA_RELATORIO_SUPRIMENTOS"\r\n'
    )

    dados += (
        b"@PJL ENTER LANGUAGE=PCL\r\n"
    )

    # ========================================================
    # RESET
    # ========================================================

    dados += b"\x1bE"

    # ========================================================
    # PAPEL
    # A4
    # RETRATO
    # ========================================================

    dados += b"\x1b&l26A"
    dados += b"\x1b&l0O"

    # ========================================================
    # MARGEM
    # ========================================================

    dados += b"\x1b&a5L"

    # ========================================================
    # 8 LINHAS POR POLEGADA
    # ========================================================

    dados += b"\x1b&l8D"

    # ========================================================
    # LIMPAR TEXTO
    # ========================================================

    texto_limpo = (
        texto_relatorio
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    texto_limpo = texto_limpo.replace(
        "\t",
        "    "
    )

    linhas = texto_limpo.split(
        "\n"
    )

    # ========================================================
    # FONTE UNICA
    #
    # TUDO COM 10 PT
    #
    # TITULOS TAMBEM.
    # ========================================================

    fonte_corpo = (
        b"\x1b(s0p10h0s0b4099T"
    )

    dados += fonte_corpo

    # ========================================================
    # ENVIAR LINHAS
    # ========================================================

    for linha in linhas:

        # ----------------------------------------------------
        # GARANTIR MESMA FONTE PARA TODAS AS LINHAS
        # ----------------------------------------------------

        dados += fonte_corpo

        linha_bytes = linha.encode(
            "cp1252",
            errors="replace"
        )

        dados += linha_bytes
        dados += b"\r\n"

    # ========================================================
    # FORM FEED
    # ========================================================

    dados += b"\x0c"

    # ========================================================
    # FIM DO JOB
    # ========================================================

    dados += b"\x1b%-12345X"

    return dados


# ============================================================
# ENVIAR PARA A LEXMARK
# ============================================================

def imprimir(
    dados,
    ip=IP_IMPRESSORA,
    porta=PORTA_RAW
):

    with socket.create_connection(
        (ip, porta),
        timeout=10
    ) as sock:

        sock.sendall(
            dados
        )


# ============================================================
# COLETA COMPLETA
#
# NAO ALTERADA.
# ============================================================

async def coletar_dados(
    ip
):

    print()

    print(
        "============================================"
    )

    print(
        "PRINTER ASSISTANT"
    )

    print(
        "RELATORIO DE CONFIGURACAO E SUPRIMENTOS"
    )

    print(
        "============================================"
    )

    print()

    print(
        "Impressora:",
        ip
    )

    print()

    print(
        "Coletando PJL + SYSDEBUG + SNMP..."
    )

    device = PrinterDevice(
        ip=ip
    )

    await device.coletar()

    identificacao = (
        device.identificacao
    )

    supplies = (
        device.supplies
    )

    print(
        "Consultando firmware via PJL..."
    )

    pjl = PJLPrinter(
        ip=ip
    )

    info_config = pjl.info_config()

    firmware = extrair_firmware(
        info_config
    )

    return (
        identificacao,
        supplies,
        firmware
    )


# ============================================================
# EXECUCAO
# ============================================================

async def executar():

    (
        identificacao,
        supplies,
        firmware
    ) = await coletar_dados(
        IP_IMPRESSORA
    )

    print()

    print(
        "Montando relatorio..."
    )

    texto_relatorio = montar_texto(
        identificacao,
        supplies,
        firmware
    )

    print()

    print(
        texto_relatorio
    )

    print()

    print(
        "Gerando PCL..."
    )

    dados = gerar_pcl(
        texto_relatorio
    )

    print(
        "Enviando para a Lexmark..."
    )

    imprimir(
        dados,
        IP_IMPRESSORA,
        PORTA_RAW
    )

    print()

    print(
        "RELATORIO ENVIADO COM SUCESSO."
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        executar()
    )