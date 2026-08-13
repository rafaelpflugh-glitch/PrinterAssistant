"""
Printer Assistant - Lexmark PJL Variable Probe

Consulta variaveis PJL comuns e extensoes Lexmark.

IMPORTANTE:
- Nenhum SET
- Nenhum DEFAULT
- Nenhum RESET
- Nenhum job
- Nenhuma alteracao permanente

O objetivo e descobrir quais variaveis realmente existem
e quais retornam valores uteis na Lexmark MX611dhe.
"""

import socket
import time


RAW_PORT = 9100
TIMEOUT = 3.0
RETRIES = 3


ESC = b"\x1b"
UEL = ESC + b"%-12345X"


def conectar(ip):
    ultimo_erro = None

    for tentativa in range(1, RETRIES + 1):
        try:
            print(
                f"Conectando em {ip}:{RAW_PORT} "
                f"(tentativa {tentativa}/{RETRIES})..."
            )

            sock = socket.create_connection(
                (ip, RAW_PORT),
                timeout=TIMEOUT,
            )

            sock.settimeout(TIMEOUT)
            return sock

        except Exception as exc:
            ultimo_erro = exc

            if tentativa < RETRIES:
                time.sleep(0.5)

    raise ultimo_erro


def enviar_consulta(ip, comando):
    dados = (
        UEL
        + comando.encode("ascii")
        + b"\r\n"
        + UEL
    )

    sock = conectar(ip)

    try:
        sock.sendall(dados)

        resposta = bytearray()

        inicio = time.time()

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta.extend(bloco)

                if b"\x0c" in bloco:
                    break

                if len(resposta) >= 16384:
                    break

            except socket.timeout:
                break

        tempo = time.time() - inicio

        texto = bytes(resposta)

        texto = texto.replace(b"\x00", b"")
        texto = texto.replace(b"\x0c", b"")
        texto = texto.replace(b"\x1b", b"")

        return texto.decode("latin-1", errors="replace").strip(), tempo

    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        sock.close()


def consultar(ip, variavel):
    comando = f"@PJL INQUIRE {variavel}"

    resposta, tempo = enviar_consulta(ip, comando)

    if not resposta:
        return "(sem resposta)", tempo

    linhas = []

    for linha in resposta.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        if linha.startswith("@PJL"):
            continue

        linhas.append(linha)

    if not linhas:
        return resposta, tempo

    return " | ".join(linhas), tempo


def consultar_default(ip, variavel):
    comando = f"@PJL DINQUIRE {variavel}"

    resposta, tempo = enviar_consulta(ip, comando)

    if not resposta:
        return "(sem resposta)", tempo

    linhas = []

    for linha in resposta.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        if linha.startswith("@PJL"):
            continue

        linhas.append(linha)

    if not linhas:
        return resposta, tempo

    return " | ".join(linhas), tempo


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - LEXMARK PJL VARIABLE PROBE")
    print("=" * 72)

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP invalido.")
        return

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {RAW_PORT}")
    print()

    print("Este teste:")
    print()
    print("- NAO executa SET.")
    print("- NAO executa DEFAULT.")
    print("- NAO executa RESET.")
    print("- NAO envia jobs.")
    print("- NAO altera configuracoes.")
    print()
    print("Serão somente consultadas variaveis PJL.")
    print()

    continuar = input("Continuar? [S/N]: ").strip().upper()

    if continuar != "S":
        print("Teste cancelado.")
        return

    variaveis = [
        "PAPER",
        "MEDIATYPE",
        "MEDIAWEIGHT",
        "MEDIATEXTURE",
        "DUPLEX",
        "RESOLUTION",
        "ORIENTATION",
        "COPIES",
        "DENSITY",
        "PAPERLENGTH",
        "PAPERWIDTH",
        "MEDIASOURCE",
        "TRAY",
        "INPUTTRAY",
        "OUTPUTBIN",
        "LANG",
        "TIMEZONE",
        "COUNTRY",
        "COUNTRYCODE",
        "LANGUAGE",
        "JOBNAME",
        "USERNAME",
        "USTATUS",
        "DISPLAY",
        "SERIALNUMBER",
        "FIRMWARE",
    ]

    print()
    print("=" * 72)
    print("1. CONSULTAS PJL")
    print("=" * 72)

    resultados = []

    for variavel in variaveis:
        print()
        print("-" * 72)
        print(f"VARIAVEL: {variavel}")
        print("-" * 72)

        try:
            corrente, tempo_corrente = consultar(
                ip,
                variavel,
            )

            print(f"INQUIRE  : {corrente}")
            print(f"Tempo    : {tempo_corrente:.3f}s")

        except Exception as exc:
            corrente = f"(erro: {exc})"
            print(f"INQUIRE  : {corrente}")
            tempo_corrente = 0.0

        try:
            padrao, tempo_padrao = consultar_default(
                ip,
                variavel,
            )

            print(f"DINQUIRE : {padrao}")
            print(f"Tempo    : {tempo_padrao:.3f}s")

        except Exception as exc:
            padrao = f"(erro: {exc})"
            print(f"DINQUIRE : {padrao}")
            tempo_padrao = 0.0

        resultados.append(
            (
                variavel,
                corrente,
                padrao,
            )
        )

    print()
    print("=" * 72)
    print("2. RESUMO")
    print("=" * 72)

    for variavel, corrente, padrao in resultados:
        print()
        print(f"{variavel}")
        print(f"  CURRENT = {corrente}")
        print(f"  DEFAULT = {padrao}")

    print()
    print("=" * 72)
    print("3. RESULTADO")
    print("=" * 72)

    print()
    print(
        "Nenhuma configuracao foi alterada."
    )

    print(
        "Nenhum DEFAULT foi alterado."
    )

    print(
        "Nenhum job foi enviado."
    )

    print()
    print(
        "Os resultados devem ser usados para identificar "
        "as variaveis realmente suportadas pela MX611."
    )

    print()
    print("Conexao RAW encerrada.")


if __name__ == "__main__":
    main()