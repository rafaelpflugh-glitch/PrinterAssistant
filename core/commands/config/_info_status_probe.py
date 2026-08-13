"""
PRINTER ASSISTANT - MX611 INFO STATUS PROBE

Consulta exclusivamente informações PJL da impressora.

NÃO executa:
- SET
- DEFAULT
- RESET
- jobs
- impressão
- alteração de configuração

Objetivo:
mapear INFO STATUS, PAGECOUNT, MEMORY, VARIABLES,
USTATUS, ID e CONFIG da Lexmark MX611dhe.
"""

from __future__ import annotations

import socket
import time


RAW_PORT = 9100
TIMEOUT = 5.0
RETRIES = 3

ESC = b"\x1b"
UEL = b"\x1b%-12345X"

IP = input("Digite o IP da impressora: ").strip()


def conectar():
    ultimo_erro = None

    for tentativa in range(1, RETRIES + 1):
        print(
            f"Conectando em {IP}:{RAW_PORT} "
            f"(tentativa {tentativa}/{RETRIES})..."
        )

        try:
            sock = socket.create_connection(
                (IP, RAW_PORT),
                timeout=TIMEOUT,
            )

            sock.settimeout(TIMEOUT)
            print("Conectado.")
            return sock

        except Exception as exc:
            ultimo_erro = exc

            if tentativa < RETRIES:
                time.sleep(0.5)

    raise ultimo_erro


def enviar_comando(comando: str) -> tuple[str, float]:
    """
    Envia uma consulta PJL e retorna a resposta completa.
    """

    payload = (
        UEL
        + comando.encode("ascii")
        + b"\r\n"
        + UEL
    )

    inicio = time.perf_counter()

    sock = conectar()

    try:
        sock.sendall(payload)

        dados = bytearray()

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                dados.extend(bloco)

                # PJL normalmente termina a resposta com FF.
                if b"\x0c" in dados:
                    break

            except socket.timeout:
                break

        resposta = bytes(dados)

    finally:
        sock.close()

    tempo = time.perf_counter() - inicio

    texto = resposta.decode(
        "latin-1",
        errors="replace",
    )

    texto = texto.replace("\x00", "")
    texto = texto.replace("\x0c", "")
    texto = texto.strip()

    return texto, tempo


def mostrar_info(categoria: str):
    print()
    print("-" * 72)
    print(f"@PJL INFO {categoria}")
    print("-" * 72)

    resposta, tempo = enviar_comando(
        f"@PJL INFO {categoria}"
    )

    print(resposta if resposta else "(sem resposta)")
    print()
    print(f"Tempo: {tempo:.3f}s")


def main():

    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 INFO STATUS PROBE")
    print("=" * 72)

    print()
    print(f"Impressora: {IP}")
    print(f"RAW:        {RAW_PORT}")

    print()
    print("Este teste:")
    print()
    print("- NÃO executa SET.")
    print("- NÃO executa DEFAULT.")
    print("- NÃO executa RESET.")
    print("- NÃO envia jobs.")
    print("- NÃO imprime.")
    print("- NÃO altera configurações.")
    print()
    print("Serão somente consultadas categorias INFO PJL.")
    print()

    confirmar = input("Continuar? [S/N]: ").strip().upper()

    if confirmar != "S":
        print("Cancelado.")
        return

    categorias = [
        "ID",
        "STATUS",
        "PAGECOUNT",
        "MEMORY",
        "VARIABLES",
        "USTATUS",
        "CONFIG",
    ]

    print()
    print("=" * 72)
    print("INÍCIO DAS CONSULTAS")
    print("=" * 72)

    resultados = {}

    for categoria in categorias:

        try:
            resposta, tempo = enviar_comando(
                f"@PJL INFO {categoria}"
            )

            resultados[categoria] = resposta

            print()
            print("=" * 72)
            print(f"INFO {categoria}")
            print("=" * 72)

            if resposta:
                print(resposta)
            else:
                print("(sem resposta)")

            print()
            print(f"Tempo: {tempo:.3f}s")

        except Exception as exc:

            resultados[categoria] = None

            print()
            print("=" * 72)
            print(f"INFO {categoria}")
            print("=" * 72)

            print(f"ERRO: {exc}")

    print()
    print("=" * 72)
    print("RESUMO")
    print("=" * 72)

    for categoria in categorias:

        resposta = resultados.get(categoria)

        if resposta:
            estado = "RESPOSTA"
        else:
            estado = "SEM RESPOSTA"

        print(
            f"{categoria:<12} {estado}"
        )

    print()
    print("Nenhuma configuração foi alterada.")
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum job foi enviado.")
    print("Nenhuma página foi impressa.")
    print()
    print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()