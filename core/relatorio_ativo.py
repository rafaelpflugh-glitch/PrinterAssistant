import socket

from core.pjl import PJLPrinter


# ============================================================
# TSC - ETIQUETADORA GRANDE
# ============================================================

IMPRESSORA = "192.168.14.151"
PORTA = 9100

LEXMARK = "192.168.14.134"


# ============================================================
# GERAR RELATORIO DE ATIVO
# ============================================================

def gerar_etiqueta_ativo(fabricante, modelo, serial, contador):

    fabricante = str(fabricante or "DESCONHECIDO")
    modelo = str(modelo or "DESCONHECIDO")
    serial = str(serial or "SEM SERIAL")
    contador = str(contador)

    tspl = ""

    # --------------------------------------------------------
    # CONFIGURACAO DA ETIQUETA
    # --------------------------------------------------------

    tspl += "SIZE 100 mm,150 mm\r\n"
    tspl += "GAP 2 mm,0 mm\r\n"
    tspl += "REFERENCE 0,0\r\n"
    tspl += "CODEPAGE 1252\r\n"
    tspl += "CLS\r\n"


    # --------------------------------------------------------
    # TITULO
    # --------------------------------------------------------

    tspl += 'TEXT 60,50,"3",0,1,1,"PRINTER ASSISTANT"\r\n'

    tspl += 'TEXT 60,100,"2",0,2,2,"RELATORIO DE ATIVO"\r\n'


    # --------------------------------------------------------
    # FABRICANTE
    # --------------------------------------------------------

    tspl += 'TEXT 60,220,"1",0,2,2,"FABRICANTE"\r\n'

    tspl += (
        f'TEXT 60,260,"2",0,2,2,"{fabricante}"\r\n'
    )


    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------

    tspl += 'TEXT 60,380,"1",0,2,2,"MODELO"\r\n'

    tspl += (
        f'TEXT 60,420,"2",0,2,2,"{modelo}"\r\n'
    )


    # --------------------------------------------------------
    # NUMERO DE SERIE
    # --------------------------------------------------------

    tspl += 'TEXT 60,540,"1",0,2,2,"NUMERO DE SERIE"\r\n'

    tspl += (
        f'TEXT 60,580,"2",0,2,2,"{serial}"\r\n'
    )


    # --------------------------------------------------------
    # CODIGO DE BARRAS
    #
    # MESMO TAMANHO QUE JA FUNCIONOU
    # A PROPRIA TSC GERA A LEGENDA
    # --------------------------------------------------------

    tspl += (
        f'BARCODE 100,700,"128",140,1,0,3,3,"{serial}"\r\n'
    )


    # --------------------------------------------------------
    # CONTADOR
    #
    # SUBSTITUI O ANTIGO "ATIVO"
    # --------------------------------------------------------

    tspl += (
        f'TEXT 60,980,"1",0,2,2,"CONTADOR: {contador}"\r\n'
    )


    # --------------------------------------------------------
    # UMA UNICA ETIQUETA
    # --------------------------------------------------------

    tspl += "PRINT 1\r\n"

    return tspl.encode(
        "cp1252",
        errors="replace"
    )


# ============================================================
# OBTER CONTADOR REAL DA LEXMARK
# ============================================================

def obter_contador():

    print()
    print("Consultando contador real da Lexmark...")
    print("Lexmark:", LEXMARK)

    impressora = PJLPrinter(
        LEXMARK
    )

    dados = impressora.coletar()

    contador = dados.get(
        "contador"
    )

    if contador is None:

        raise RuntimeError(
            "Nao foi possivel obter o contador real da Lexmark."
        )

    print(
        "Contador real:",
        contador
    )

    return contador


# ============================================================
# ENVIAR PARA A TSC
# ============================================================

def imprimir_relatorio_ativo(
    fabricante,
    modelo,
    serial,
    contador,
    ip=IMPRESSORA,
    porta=PORTA
):

    dados = gerar_etiqueta_ativo(
        fabricante,
        modelo,
        serial,
        contador
    )

    print()
    print("========================================")
    print("PRINTER ASSISTANT")
    print("RELATORIO DE ATIVO")
    print("========================================")
    print()
    print("TSC:", ip)
    print("MODELO:", modelo)
    print("SERIAL:", serial)
    print("CONTADOR:", contador)
    print()
    print("Enviando etiqueta...")

    with socket.create_connection(
        (ip, porta),
        timeout=10
    ) as sock:

        sock.sendall(
            dados
        )

    print("Etiqueta enviada.")
    print()


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    fabricante = "Lexmark"
    modelo = "MX611dhe"
    serial = "701644HH03ND3"

    try:

        contador = obter_contador()

    except Exception as erro:

        print()
        print("ERRO AO OBTER CONTADOR:")
        print(erro)
        print()
        print("Etiqueta NAO sera impressa.")
        raise SystemExit(1)


    imprimir_relatorio_ativo(
        fabricante=fabricante,
        modelo=modelo,
        serial=serial,
        contador=contador
    )
