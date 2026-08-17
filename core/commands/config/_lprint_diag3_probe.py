"""
PRINTER ASSISTANT
MX611 - LPRINT DIAG3 ISOLATED PROBE

Investiga exclusivamente:

    @PJL LPRINTDIAG3TEST

IMPORTANTE:
Este teste NÃO executa:
    - RESET
    - DEFAULT
    - SET
    - firmware
    - jobs PCL
    - jobs PostScript

Objetivo:
Determinar se LPRINTDIAG3TEST pode ser enviado
isoladamente para a MX611 e observar seu comportamento.
"""

from __future__ import annotations

import socket
import time


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DEFAULT_IP = "192.168.14.134"

RAW_PORT = 9100

CONNECT_TIMEOUT = 5.0

READ_TIMEOUT = 5.0


# ============================================================
# PJL
# ============================================================

COMMAND = "@PJL LPRINTDIAG3TEST"


def build_payload() -> bytes:

    payload = (
        "\x1b%-12345X"
        "@PJL\n"
        f"{COMMAND}\n"
        "\x1b%-12345X"
    )

    return payload.encode(
        "latin-1",
        errors="replace",
    )


# ============================================================
# TESTE
# ============================================================

def execute(ip: str) -> None:

    print()
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 DIAG3 ISOLATED PROBE")
    print("=" * 72)

    print()

    print(f"Impressora : {ip}")
    print(f"RAW        : {RAW_PORT}")
    print(f"Comando    : {COMMAND}")

    print()

    print("ATENÇÃO:")
    print()
    print("Este comando pode produzir atividade física")
    print("e/ou impressão na impressora.")
    print()
    print("Observe a MX611 durante todo o teste.")

    print()

    answer = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if answer != "S":
        print()
        print("Teste cancelado.")
        return

    payload = build_payload()

    print()
    print("=" * 72)
    print("INICIANDO TESTE")
    print("=" * 72)

    print()

    started = time.perf_counter()

    try:

        print(
            f"Conectando em "
            f"{ip}:{RAW_PORT}..."
        )

        connect_started = time.perf_counter()

        sock = socket.create_connection(
            (
                ip,
                RAW_PORT,
            ),
            timeout=CONNECT_TIMEOUT,
        )

        connect_elapsed = (
            time.perf_counter()
            - connect_started
        )

        print(
            f"Conectado em "
            f"{connect_elapsed:.3f}s."
        )

        try:

            sock.settimeout(
                READ_TIMEOUT
            )

            print()

            print("Enviando PJL...")

            send_started = time.perf_counter()

            sock.sendall(
                payload
            )

            send_elapsed = (
                time.perf_counter()
                - send_started
            )

            print(
                f"Envio concluído em "
                f"{send_elapsed:.3f}s."
            )

            print()

            print(
                "Comando enviado."
            )

            print(
                "Aguardando eventual resposta..."
            )

            chunks: list[bytes] = []

            read_started = time.perf_counter()

            while True:

                try:

                    data = sock.recv(
                        4096
                    )

                except socket.timeout:

                    read_elapsed = (
                        time.perf_counter()
                        - read_started
                    )

                    print()

                    print(
                        "READ TIMEOUT."
                    )

                    print(
                        f"Tempo de leitura: "
                        f"{read_elapsed:.3f}s"
                    )

                    break

                if not data:

                    print()

                    print(
                        "Socket encerrado pela impressora."
                    )

                    break

                chunks.append(
                    data
                )

        finally:

            sock.close()

    except socket.timeout as exc:

        elapsed = (
            time.perf_counter()
            - started
        )

        print()
        print("TIMEOUT DE CONEXÃO.")
        print()
        print(f"Detalhe : {exc}")
        print(f"Tempo   : {elapsed:.3f}s")

        print()
        print(
            "A porta 9100 não aceitou a conexão "
            "dentro do tempo configurado."
        )

        return

    except OSError as exc:

        elapsed = (
            time.perf_counter()
            - started
        )

        print()
        print("ERRO DE COMUNICAÇÃO.")
        print()
        print(f"Tipo    : {type(exc).__name__}")
        print(f"Detalhe : {exc}")
        print(f"Tempo   : {elapsed:.3f}s")

        return

    response = (
        b"".join(chunks)
        .decode(
            "latin-1",
            errors="replace",
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    print()
    print("=" * 72)
    print("RESULTADO DA COMUNICAÇÃO")
    print("=" * 72)

    print()

    if response:

        print("RESPOSTA RECEBIDA:")
        print()
        print("-" * 72)
        print(response)
        print("-" * 72)

    else:

        print(
            "Nenhuma resposta PJL recebida."
        )

    print()

    print(
        f"Tempo total: {elapsed:.3f}s"
    )

    print()

    print("=" * 72)
    print("OBSERVAÇÃO FÍSICA")
    print("=" * 72)

    print()

    print(
        "Agora observe o que aconteceu na impressora."
    )

    print()

    print(
        "Anote exatamente:"
    )

    print(
        "  1. Imprimiu alguma página?"
    )

    print(
        "  2. Qual página?"
    )

    print(
        "  3. Quantas páginas?"
    )

    print(
        "  4. A página saiu normalmente?"
    )

    print(
        "  5. Houve atolamento?"
    )

    print(
        "  6. Houve mensagem no painel?"
    )

    print(
        "  7. A impressora ficou ocupada?"
    )

    print(
        "  8. Depois voltou para Ready?"
    )

    print()

    print("=" * 72)
    print("FIM DO TESTE")
    print("=" * 72)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    ip = input(
        f"Digite o IP da impressora "
        f"[{DEFAULT_IP}]: "
    ).strip()

    if not ip:
        ip = DEFAULT_IP

    execute(ip)


if __name__ == "__main__":
    main()