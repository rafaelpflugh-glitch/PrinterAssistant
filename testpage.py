import socket
import sys
import json
from pathlib import Path
from datetime import datetime


# ============================================================
# PRINTER ASSISTANT - PÁGINA DE TESTE
# ============================================================
#
# Objetivo:
#
# Gerar e enviar uma página de teste diretamente para uma
# impressora laser através da porta RAW 9100.
#
# A página contém:
#
# - identificação do equipamento
# - preto chapado
# - branco
# - escala de cinza
# - linhas horizontais
# - linhas verticais
# - texto pequeno
# - padrão repetitivo
#
# Compatível inicialmente com impressoras que aceitam
# PCL/RAW pela porta 9100.
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

PRINTER_DATA = BASE_DIR / "printer_data.json"

PORTA_PADRAO = 9100

TIMEOUT = 5


# ============================================================
# CORES / PCL
# ============================================================

ESC = b"\x1b"

PCL_RESET = ESC + b"E"

PCL_PORTRAIT = ESC + b"&l0O"

PCL_A4 = ESC + b"&l26A"

PCL_MARGIN = ESC + b"&l0E"

PCL_RESOLUTION = ESC + b"*t600R"


# ============================================================
# CARREGAR DADOS
# ============================================================

def carregar_dados():

    if not PRINTER_DATA.exists():

        return {}


    try:

        with open(
            PRINTER_DATA,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)


    except Exception:

        return {}


# ============================================================
# ENTRADA DO IP
# ============================================================

def solicitar_ip():

    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()


    if not ip:

        raise ValueError(
            "IP não informado."
        )


    return ip


# ============================================================
# IDENTIFICAÇÃO
# ============================================================

def obter_identificacao():

    dados = carregar_dados()

    identificacao = dados.get(
        "identificacao",
        {}
    )


    modelo = identificacao.get(
        "modelo",
        "Desconhecido"
    )


    serial = identificacao.get(
        "serial",
        "Desconhecido"
    )


    contador = identificacao.get(
        "contador"
    )


    if contador is None:

        contador_texto = "N/A"

    else:

        contador_texto = (
            f"{contador:,}".replace(
                ",",
                "."
            )
        )


    return {

        "modelo": modelo,

        "serial": serial,

        "contador": contador_texto

    }


# ============================================================
# COMANDOS PCL
# ============================================================

def cursor(x, y):

    # PCL utiliza coordenadas decipoint.
    #
    # 1/720 polegada.
    #
    # A4:
    # 210 x 297 mm
    #
    # Conversão aproximada:
    # 1 mm = 28.35 decipoints

    x_pcl = int(x * 28.35)

    y_pcl = int(y * 28.35)


    return (
        ESC
        + f"*p{x_pcl}X".encode()
        + ESC
        + f"*p{y_pcl}Y".encode()
    )


def fonte(tamanho=12):

    return (
        ESC
        + f"(s{tamanho}V".encode()
    )


def texto(conteudo):

    return (
        conteudo
        .encode(
            "cp850",
            errors="replace"
        )
    )


# ============================================================
# RETÂNGULO PREENCHIDO
# ============================================================

def retangulo_preenchido(
    x,
    y,
    largura,
    altura,
    densidade=100
):

    dados = b""


    dados += cursor(
        x,
        y
    )


    # Define padrão de preenchimento.
    #
    # PCL:
    # ESC *c#G
    #
    # 0 = branco
    # 1 = preto
    #
    # Para esta primeira versão usamos preto sólido.

    if densidade >= 100:

        dados += (
            ESC
            + b"*c1G"
        )

    else:

        dados += (
            ESC
            + b"*c2G"
        )


    dados += (
        ESC
        + f"*c{int(largura * 28.35)}a"
        .encode()
    )


    dados += (
        ESC
        + f"*c{int(altura * 28.35)}b"
        .encode()
    )


    dados += (
        ESC
        + b"*c0P"
    )


    return dados


# ============================================================
# LINHA
# ============================================================

def linha(
    x1,
    y1,
    x2,
    y2
):

    dados = b""


    dados += cursor(
        x1,
        y1
    )


    dados += (
        ESC
        + b"*c1P"
    )


    dados += (
        ESC
        + f"*c{x2 * 28.35:.0f}A".encode()
    )


    dados += (
        ESC
        + f"*c{y2 * 28.35:.0f}B".encode()
    )


    return dados


# ============================================================
# CONSTRUIR PÁGINA
# ============================================================

def construir_pagina():

    info = obter_identificacao()


    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )


    dados = b""


    # --------------------------------------------------------
    # INICIALIZAÇÃO
    # --------------------------------------------------------

    dados += PCL_RESET

    dados += PCL_PORTRAIT

    dados += PCL_A4

    dados += PCL_MARGIN

    dados += PCL_RESOLUTION


    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    dados += cursor(
        15,
        15
    )


    dados += fonte(
        22
    )


    dados += texto(
        "PRINTER ASSISTANT"
    )


    dados += cursor(
        15,
        25
    )


    dados += fonte(
        12
    )


    dados += texto(
        "PAGINA DE TESTE - LASER MONOCROMATICA"
    )


    dados += cursor(
        15,
        32
    )


    dados += texto(
        f"Modelo: {info['modelo']}"
    )


    dados += cursor(
        15,
        39
    )


    dados += texto(
        f"Serial: {info['serial']}"
    )


    dados += cursor(
        15,
        46
    )


    dados += texto(
        f"Contador: {info['contador']} paginas"
    )


    dados += cursor(
        15,
        53
    )


    dados += texto(
        f"Teste realizado: {agora}"
    )


    # --------------------------------------------------------
    # BORDA
    # --------------------------------------------------------

    dados += cursor(
        10,
        60
    )


    dados += texto(
        "+" + "-" * 70 + "+"
    )


    # --------------------------------------------------------
    # PRETO CHAPADO
    # --------------------------------------------------------

    dados += cursor(
        15,
        68
    )


    dados += fonte(
        16
    )


    dados += texto(
        "PRETO CHAPADO - 100%"
    )


    dados += retangulo_preenchido(
        15,
        75,
        180,
        35,
        100
    )


    # --------------------------------------------------------
    # ÁREA BRANCA
    # --------------------------------------------------------

    dados += cursor(
        15,
        120
    )


    dados += fonte(
        16
    )


    dados += texto(
        "AREA BRANCA"
    )


    dados += cursor(
        15,
        127
    )


    dados += fonte(
        12
    )


    dados += texto(
        "Observe fundo, manchas, sujeira e cinzentamento."
    )


    # --------------------------------------------------------
    # LINHAS FINAS
    # --------------------------------------------------------

    dados += cursor(
        15,
        142
    )


    dados += fonte(
        16
    )


    dados += texto(
        "LINHAS HORIZONTAIS"
    )


    y = 150


    for espaco in (
        1,
        2,
        3,
        4,
        5
    ):

        for _ in range(3):

            dados += linha(
                15,
                y,
                195,
                y
            )

            y += espaco


        y += 2


    # --------------------------------------------------------
    # TEXTO PEQUENO
    # --------------------------------------------------------

    dados += cursor(
        15,
        188
    )


    dados += fonte(
        10
    )


    dados += texto(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )


    dados += cursor(
        15,
        194
    )


    dados += texto(
        "abcdefghijklmnopqrstuvwxyz"
    )


    dados += cursor(
        15,
        200
    )


    dados += texto(
        "0123456789  !@#$%&*()  1234567890"
    )


    # --------------------------------------------------------
    # PADRÃO REPETITIVO
    # --------------------------------------------------------

    dados += cursor(
        15,
        212
    )


    dados += fonte(
        16
    )


    dados += texto(
        "PADRAO REPETITIVO"
    )


    dados += cursor(
        15,
        220
    )


    dados += fonte(
        12
    )


    for _ in range(12):

        dados += texto(
            "||||||||||||||||||||||||||||||||||||||||"
        )

        dados += cursor(
            15,
            220 + (_ + 1) * 4
        )


    # --------------------------------------------------------
    # BLOCO FINAL
    # --------------------------------------------------------

    dados += cursor(
        15,
        272
    )


    dados += fonte(
        12
    )


    dados += texto(
        "FIM DO TESTE - PRINTER ASSISTANT"
    )


    # --------------------------------------------------------
    # FINALIZA PÁGINA
    # --------------------------------------------------------

    dados += b"\x0c"


    return dados


# ============================================================
# ENVIAR PARA IMPRESSORA
# ============================================================

def enviar_impressora(
    ip,
    dados
):

    print()

    print(
        f"Conectando em {ip}:{PORTA_PADRAO}..."
    )


    sock = None


    try:

        sock = socket.create_connection(

            (
                ip,
                PORTA_PADRAO
            ),

            timeout=TIMEOUT

        )


        print(
            "Conexão RAW estabelecida."
        )


        sock.sendall(
            dados
        )


        print(
            "Página enviada para a impressora."
        )


        return True


    except Exception as erro:

        print()

        print(
            "ERRO ao enviar página:"
        )


        print(
            erro
        )


        return False


    finally:

        if sock:

            try:

                sock.close()

            except:

                pass


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - PAGINA DE TESTE"
    )

    print("=" * 60)


    try:

        ip = solicitar_ip()


    except ValueError as erro:

        print()

        print(
            erro
        )

        return


    info = obter_identificacao()


    print()

    print(
        "Equipamento:"
    )


    print(
        f"Modelo : {info['modelo']}"
    )


    print(
        f"Serial : {info['serial']}"
    )


    print(
        f"Contador: {info['contador']}"
    )


    print()

    print(
        "Construindo página de teste..."
    )


    pagina = construir_pagina()


    print(
        f"Tamanho: {len(pagina):,} bytes"
    )


    sucesso = enviar_impressora(
        ip,
        pagina
    )


    print()

    print("=" * 60)


    if sucesso:

        print(
            "TESTE ENVIADO COM SUCESSO"
        )


    else:

        print(
            "FALHA NO ENVIO"
        )


    print("=" * 60)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()