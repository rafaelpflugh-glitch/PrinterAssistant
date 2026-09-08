import socket
import re


LEXMARK_IP = "192.168.14.134"
TSC_IP = "192.168.14.151"

TSC_PORT = 9100


def obter_contador():

    pjl = b"\x1b%-12345X"
    pjl += b"@PJL INFO PAGECOUNT\r\n"
    pjl += b"\x1b%-12345X"

    with socket.create_connection(
        (LEXMARK_IP, 9100),
        timeout=10
    ) as sock:

        sock.sendall(pjl)

        resposta = b""

        sock.settimeout(3)

        while True:

            try:
                parte = sock.recv(4096)

            except socket.timeout:
                break

            if not parte:
                break

            resposta += parte

            if len(parte) < 4096:
                break

    texto = resposta.decode(
        "latin1",
        errors="ignore"
    )

    print("Resposta PAGECOUNT:")
    print(repr(texto))

    padroes = [
        r"PAGECOUNT\s+(\d+)",
        r"PAGECOUNT\s*=\s*(\d+)",
        r"PAGE_COUNT\s*=\s*(\d+)",
        r"PAGES\s*=\s*(\d+)"
    ]

    for padrao in padroes:

        resultado = re.search(
            padrao,
            texto,
            re.IGNORECASE
        )

        if resultado:

            return int(
                resultado.group(1)
            )

    return None


def gerar_etiqueta(contador):

    pjl = b"\x1b%-12345X"

    pjl += (
        b"@PJL JOB NAME=\"PRINTER_ASSISTANT_ATIVO\"\r\n"
    )

    pjl += b"@PJL ENTER LANGUAGE=PCL\r\n"

    # Inicializa PCL
    pjl += b"\x1bE"

    # Courier 12
    pjl += b"\x1b(s0p12h0s0b4099T"

    # -------------------------------------------------
    # RELATORIO
    # -------------------------------------------------

    pjl += b"\r\n"

    pjl += b"PRINTER ASSISTANT\r\n"
    pjl += b"\r\n"

    pjl += b"RELATORIO DE ATIVO\r\n"

    pjl += b"\r\n"

    pjl += b"FABRICANTE: Lexmark\r\n"
    pjl += b"MODELO:     MX611dhe\r\n"
    pjl += b"SERIAL:     701644HH03ND3\r\n"

    pjl += b"\r\n"

    pjl += (
        b"CODIGO DE BARRAS:\r\n"
    )

    pjl += b"\r\n"

    # C?digo Code 39 simples.
    # A TSC imprime a representa??o textual.
    # Depois substitu?mos pelo barcode real da etiqueta.

    pjl += (
        b"*701644HH03ND3*\r\n"
    )

    pjl += b"\r\n"

    pjl += (
        b"CONTADOR: "
        + str(contador).encode("ascii")
        + b"\r\n"
    )

    # Uma ?nica p?gina
    pjl += b"\x0c"

    # Finaliza
    pjl += b"\x1b%-12345X"

    pjl += (
        b"@PJL EOJ "
        b"NAME=\"PRINTER_ASSISTANT_ATIVO\"\r\n"
    )

    pjl += b"\x1b%-12345X"

    return pjl


def imprimir(dados):

    with socket.create_connection(
        (TSC_IP, TSC_PORT),
        timeout=10
    ) as sock:

        sock.sendall(dados)


def main():

    print("=" * 50)
    print("PRINTER ASSISTANT")
    print("TESTE RELATORIO DE ATIVO")
    print("=" * 50)

    print()
    print("Lexmark:", LEXMARK_IP)
    print("TSC:", TSC_IP)
    print()

    print("Consultando contador real...")

    contador = obter_contador()

    if contador is None:

        print()
        print("ERRO: contador nao encontrado.")
        print("Etiqueta NAO sera enviada.")
        return

    print()
    print("CONTADOR REAL:", contador)

    print()
    print("Montando etiqueta...")

    dados = gerar_etiqueta(
        contador
    )

    print(
        "Tamanho do job:",
        len(dados),
        "bytes"
    )

    print()
    print("Enviando para TSC...")

    imprimir(
        dados
    )

    print()
    print("Etiqueta enviada.")
    print()


if __name__ == "__main__":
    main()
