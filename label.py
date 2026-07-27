import socket
from pathlib import Path
import json


# ============================================================
# PRINTER ASSISTANT - LABEL
# ============================================================
#
# Impressão de etiqueta de ativo em etiquetadora TSC
# utilizando TSPL diretamente pela rede.
#
# Etiqueta:
#   100 x 150 mm
#
# Conteúdo:
#   fabricante + modelo
#   número de série
#   código de barras Code 128
#   contador de páginas
#
# ============================================================


# ============================================================
# CONFIGURAÇÃO
# ============================================================

LABEL_PRINTER_IP = "192.168.14.151"

LABEL_PRINTER_PORT = 9100

# Dimensões físicas da etiqueta
LABEL_WIDTH_MM = 100
LABEL_HEIGHT_MM = 150

# Resolução padrão da TSC
DPI = 203

# Arquivo produzido pelo collector.py
PRINTER_DATA = (
    Path(__file__).resolve().parent
    / "printer_data.json"
)


# ============================================================
# CONVERSÃO MM -> DOTS
# ============================================================

def mm_para_dots(mm):
    """
    Converte milímetros para pontos da impressora.
    """

    return int(
        mm * DPI / 25.4
    )


# ============================================================
# ESCAPAR TEXTO TSPL
# ============================================================

def limpar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)

    # Evita problemas com aspas
    texto = texto.replace(
        '"',
        "'"
    )

    # TSPL trabalha melhor com ASCII
    texto = texto.encode(
        "ascii",
        errors="replace"
    ).decode(
        "ascii"
    )

    return texto


# ============================================================
# FORMATAR NÚMERO
# ============================================================

def formatar_numero(numero):

    if numero is None:
        return "N/A"

    try:

        return f"{int(numero):,}".replace(
            ",",
            "."
        )

    except:

        return str(numero)


# ============================================================
# CARREGAR DADOS
# ============================================================

def carregar_dados():

    if not PRINTER_DATA.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado:\n{PRINTER_DATA}"
        )


    with open(
        PRINTER_DATA,
        "r",
        encoding="utf-8"
    ) as arquivo:

        dados = json.load(
            arquivo
        )


    identificacao = dados.get(
        "identificacao",
        {}
    )


    return {

        "fabricante":
            identificacao.get(
                "fabricante",
                "Desconhecido"
            ),

        "modelo":
            identificacao.get(
                "modelo",
                "Desconhecido"
            ),

        "serial":
            identificacao.get(
                "serial",
                "Desconhecido"
            ),

        "contador":
            identificacao.get(
                "contador"
            )

    }


# ============================================================
# TESTAR CONEXÃO
# ============================================================

def testar_conexao():

    print()

    print(
        f"Conectando na TSC "
        f"{LABEL_PRINTER_IP}:{LABEL_PRINTER_PORT}..."
    )


    try:

        with socket.create_connection(

            (
                LABEL_PRINTER_IP,
                LABEL_PRINTER_PORT
            ),

            timeout=5

        ):

            print(
                "Conexão com a etiquetadora OK."
            )

            return True


    except Exception as erro:

        print(
            "ERRO ao conectar na TSC:"
        )

        print(
            erro
        )

        return False


# ============================================================
# GERAR TSPL
# ============================================================

def gerar_tspl(dados):

    fabricante = limpar_texto(
        dados["fabricante"]
    )

    modelo = limpar_texto(
        dados["modelo"]
    )

    serial = limpar_texto(
        dados["serial"]
    )

    contador = formatar_numero(
        dados["contador"]
    )


    # --------------------------------------------------------
    # Dimensões em dots
    # --------------------------------------------------------

    largura = mm_para_dots(
        LABEL_WIDTH_MM
    )

    altura = mm_para_dots(
        LABEL_HEIGHT_MM
    )


    # --------------------------------------------------------
    # Coordenadas
    #
    # Etiqueta em pé:
    #
    # 100 mm largura
    # 150 mm altura
    #
    # --------------------------------------------------------

    margem_x = mm_para_dots(5)

    x = margem_x


    # --------------------------------------------------------
    # Cabeçalho
    # --------------------------------------------------------

    y_fabricante = mm_para_dots(8)

    y_modelo = mm_para_dots(22)


    # --------------------------------------------------------
    # Serial
    # --------------------------------------------------------

    y_serial_titulo = mm_para_dots(45)

    y_serial = mm_para_dots(54)


    # --------------------------------------------------------
    # Código de barras
    # --------------------------------------------------------

    y_barcode = mm_para_dots(70)

    barcode_altura = mm_para_dots(28)


    # --------------------------------------------------------
    # Contador
    # --------------------------------------------------------

    y_paginas_titulo = mm_para_dots(112)

    y_paginas = mm_para_dots(122)


    # ========================================================
    # TSPL
    # ========================================================

    comandos = []


    # --------------------------------------------------------
    # Configuração
    # --------------------------------------------------------

    comandos.append(
        f"SIZE {LABEL_WIDTH_MM} mm,{LABEL_HEIGHT_MM} mm"
    )

    comandos.append(
        "GAP 3 mm,0"
    )

    comandos.append(
        "DIRECTION 1"
    )

    comandos.append(
        "REFERENCE 0,0"
    )

    comandos.append(
        "CLS"
    )


    # ========================================================
    # FABRICANTE
    # ========================================================

    comandos.append(

        f'TEXT {x},{y_fabricante},'
        f'"3",0,1,1,"{fabricante}"'

    )


    # ========================================================
    # MODELO
    # ========================================================

    comandos.append(

        f'TEXT {x},{y_modelo},'
        f'"3",0,1,1,"{modelo}"'

    )


    # ========================================================
    # SERIAL
    # ========================================================

    comandos.append(

        f'TEXT {x},{y_serial_titulo},'
        f'"3",0,1,1,"SERIAL"'

    )


    comandos.append(

        f'TEXT {x},{y_serial},'
        f'"3",0,2,2,"{serial}"'

    )


    # ========================================================
    # CÓDIGO DE BARRAS
    # ========================================================
    #
    # CODE128
    #
    # 128 = Code 128
    #
    # rotation = 0
    # narrow = 2
    # wide = 2
    #
    # ========================================================

    comandos.append(

        f'BARCODE {x},{y_barcode},'
        f'"128",'
        f'{barcode_altura},'
        f'1,0,2,2,'
        f'"{serial}"'

    )


    # ========================================================
    # CONTADOR
    # ========================================================

    comandos.append(

        f'TEXT {x},{y_paginas_titulo},'
        f'"3",0,1,1,"PAGINAS"'

    )


    comandos.append(

        f'TEXT {x},{y_paginas},'
        f'"3",0,3,3,"{contador}"'

    )


    # ========================================================
    # IMPRIMIR
    # ========================================================

    comandos.append(
        "PRINT 1,1"
    )


    comandos.append(
        "END"
    )


    return "\r\n".join(
        comandos
    ) + "\r\n"


# ============================================================
# ENVIAR PARA TSC
# ============================================================

def imprimir(tspl):

    print()

    print(
        "Enviando etiqueta para a TSC..."
    )


    dados = tspl.encode(
        "ascii",
        errors="replace"
    )


    try:

        with socket.create_connection(

            (
                LABEL_PRINTER_IP,
                LABEL_PRINTER_PORT
            ),

            timeout=5

        ) as sock:

            sock.sendall(
                dados
            )


        print(
            "Etiqueta enviada com sucesso."
        )

        return True


    except Exception as erro:

        print(
            "ERRO durante a impressão:"
        )

        print(
            erro
        )

        return False


# ============================================================
# MOSTRAR PRÉVIA
# ============================================================

def mostrar_dados(dados):

    print()

    print("=" * 60)

    print(
        "DADOS DA ETIQUETA"
    )

    print("=" * 60)


    print()

    print(
        "Fabricante:",
        dados["fabricante"]
    )

    print(
        "Modelo:",
        dados["modelo"]
    )

    print(
        "Serial:",
        dados["serial"]
    )

    print(
        "Páginas:",
        formatar_numero(
            dados["contador"]
        )
    )

    print()

    print(
        "Etiquetadora:",
        LABEL_PRINTER_IP
    )

    print(
        "Tamanho:",
        f"{LABEL_WIDTH_MM} x {LABEL_HEIGHT_MM} mm"
    )

    print(
        "DPI:",
        DPI
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - ETIQUETA DE ATIVO"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # Dados
    # --------------------------------------------------------

    try:

        dados = carregar_dados()

    except Exception as erro:

        print()

        print(
            "ERRO:"
        )

        print(
            erro
        )

        return


    mostrar_dados(
        dados
    )


    # --------------------------------------------------------
    # Conexão
    # --------------------------------------------------------

    if not testar_conexao():

        return


    # --------------------------------------------------------
    # Gerar TSPL
    # --------------------------------------------------------

    tspl = gerar_tspl(
        dados
    )


    # --------------------------------------------------------
    # Imprimir
    # --------------------------------------------------------

    print()

    resposta = input(
        "Imprimir esta etiqueta? [S/N]: "
    ).strip().upper()


    if resposta != "S":

        print()

        print(
            "Impressão cancelada."
        )

        return


    imprimir(
        tspl
    )


    print()

    print("=" * 60)

    print(
        "FIM"
    )

    print("=" * 60)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()