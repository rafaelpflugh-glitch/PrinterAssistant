import socket
from pathlib import Path

from core.context import (
    obter_impressora_ativa,
    NoActivePrinterError
)


# ============================================================
# PRINTER ASSISTANT - LABEL
# ============================================================
#
# Impressão de etiqueta de ativo em etiquetadora TSC
# utilizando TSPL diretamente pela rede.
#
# A impressora em atendimento NÃO é informada manualmente.
#
# Ela vem da:
#
#     session.json
#
# A TSC é outro equipamento:
#
#     TSC -> 192.168.14.151:9100
#
# ============================================================


# ============================================================
# TSC
# ============================================================

LABEL_PRINTER_IP = "192.168.14.151"

LABEL_PRINTER_PORT = 9100


# ============================================================
# ETIQUETA
# ============================================================

LABEL_WIDTH_MM = 100

LABEL_HEIGHT_MM = 150


# ============================================================
# TSC 203 DPI
# ============================================================

DPI = 203


# ============================================================
# CONVERSÃO
# ============================================================

def mm_para_dots(mm):

    return int(
        mm * DPI / 25.4
    )


# ============================================================
# TEXTO
# ============================================================

def limpar_texto(texto):

    if texto is None:

        return ""


    texto = str(
        texto
    )


    texto = texto.replace(
        '"',
        "'"
    )


    # --------------------------------------------------------
    # TSPL / impressoras térmicas costumam trabalhar melhor
    # com ASCII simples.
    # --------------------------------------------------------

    texto = texto.encode(
        "ascii",
        errors="replace"
    ).decode(
        "ascii"
    )


    return texto


# ============================================================
# NÚMEROS
# ============================================================

def formatar_numero(numero):

    if numero is None:

        return "N/A"


    try:

        return f"{int(numero):,}".replace(
            ",",
            "."
        )


    except Exception:

        return str(
            numero
        )


# ============================================================
# CONEXÃO TSC
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

        print()

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
        dados.get(
            "fabricante"
        )
    )


    modelo = limpar_texto(
        dados.get(
            "modelo"
        )
    )


    serial = limpar_texto(
        dados.get(
            "serial"
        )
    )


    contador = formatar_numero(
        dados.get(
            "contador"
        )
    )


    largura = mm_para_dots(
        LABEL_WIDTH_MM
    )


    altura = mm_para_dots(
        LABEL_HEIGHT_MM
    )


    # --------------------------------------------------------
    # Margens
    # --------------------------------------------------------

    margem_x = mm_para_dots(
        6
    )


    # --------------------------------------------------------
    # Cabeçalho
    # --------------------------------------------------------

    tspl = []


    tspl.append(
        f"SIZE {LABEL_WIDTH_MM} mm,{LABEL_HEIGHT_MM} mm"
    )


    tspl.append(
        "GAP 3 mm,0 mm"
    )


    tspl.append(
        "DIRECTION 1"
    )


    tspl.append(
        "REFERENCE 0,0"
    )


    tspl.append(
        "CLS"
    )


    # ========================================================
    # TÍTULO
    # ========================================================

    tspl.append(
        'TEXT 40,40,"3",0,1,1,"PRINTER ASSISTANT"'
    )


    # ========================================================
    # FABRICANTE
    # ========================================================

    tspl.append(
        f'TEXT 40,100,"3",0,1,1,"{fabricante}"'
    )


    # ========================================================
    # MODELO
    # ========================================================

    tspl.append(
        f'TEXT 40,150,"3",0,1,1,"{modelo}"'
    )


    # ========================================================
    # LINHA
    # ========================================================

    tspl.append(
        f"BAR 40,210,{largura - 80},3"
    )


    # ========================================================
    # SERIAL
    # ========================================================

    tspl.append(
        'TEXT 40,250,"2",0,1,1,"SERIAL"'
    )


    tspl.append(
        f'TEXT 40,290,"3",0,1,1,"{serial}"'
    )


    # ========================================================
    # CÓDIGO DE BARRAS
    # ========================================================

    if serial:

        tspl.append(
            f'BARCODE 40,350,"128",100,1,0,3,3,"{serial}"'
        )


    # ========================================================
    # CONTADOR
    # ========================================================

    tspl.append(
        'TEXT 40,490,"2",0,1,1,"CONTADOR"'
    )


    tspl.append(
        f'TEXT 40,530,"3",0,1,1,"{contador}"'
    )


    # ========================================================
    # RODAPÉ
    # ========================================================

    tspl.append(
        f"BAR 40,610,{largura - 80},3"
    )


    tspl.append(
        'TEXT 40,650,"2",0,1,1,"ATIVO DE TI"'
    )


    tspl.append(
        'TEXT 40,690,"2",0,1,1,"PRINTER ASSISTANT"'
    )


    # ========================================================
    # IMPRESSÃO
    # ========================================================

    tspl.append(
        "PRINT 1,1"
    )


    tspl.append(
        ""
    )


    return "\r\n".join(
        tspl
    )


# ============================================================
# ENVIAR PARA TSC
# ============================================================

def imprimir_tspl(tspl):

    print()

    print(
        "Enviando etiqueta para TSC..."
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
                tspl.encode(
                    "ascii",
                    errors="replace"
                )
            )


        print(
            "Etiqueta enviada com sucesso."
        )

        return True


    except Exception as erro:

        print()

        print(
            "ERRO ao imprimir:"
        )

        print(
            erro
        )

        return False


# ============================================================
# MOSTRAR DADOS
# ============================================================

def mostrar_dados(dados):

    print()

    print("=" * 60)

    print(
        "IMPRESSORA ATIVA"
    )

    print("=" * 60)


    print()

    print(
        "IP:",
        dados.get(
            "ip"
        )
    )


    print(
        "Fabricante:",
        dados.get(
            "fabricante"
        )
    )


    print(
        "Modelo:",
        dados.get(
            "modelo"
        )
    )


    print(
        "Serial:",
        dados.get(
            "serial"
        )
    )


    print(
        "Contador:",
        formatar_numero(
            dados.get(
                "contador"
            )
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - ETIQUETA"
    )

    print("=" * 60)


    # ========================================================
    # CONTEXTO
    # ========================================================

    print()

    print(
        "Carregando impressora ativa..."
    )


    try:

        dados = obter_impressora_ativa()


    except NoActivePrinterError as erro:

        print()

        print(
            "ERRO:"
        )

        print(
            erro
        )

        print()

        print(
            "Primeiro execute o scanner e selecione"
        )

        print(
            "uma impressora para criar a sessão."
        )

        print()

        return


    # ========================================================
    # MOSTRAR
    # ========================================================

    mostrar_dados(
        dados
    )


    # ========================================================
    # CONFIRMAÇÃO
    # ========================================================

    print()

    resposta = input(
        "Imprimir esta etiqueta? [S/N]: "
    ).strip().upper()


    if resposta != "S":

        print()

        print(
            "Impressão cancelada."
        )

        print()

        return


    # ========================================================
    # TSC
    # ========================================================

    if not testar_conexao():

        return


    # ========================================================
    # GERAR
    # ========================================================

    tspl = gerar_tspl(
        dados
    )


    # ========================================================
    # IMPRIMIR
    # ========================================================

    imprimir_tspl(
        tspl
    )


    print()

    print("=" * 60)

    print(
        "OPERAÇÃO CONCLUÍDA"
    )

    print("=" * 60)

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()