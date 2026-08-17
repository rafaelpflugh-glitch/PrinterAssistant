"""
PRINTER ASSISTANT
MX611 EXTENDED LPRINT PROBE

Investigação controlada de comandos LPRINT adicionais.

IMPORTANTE:

Este programa NÃO:

    - executa SET
    - executa DEFAULT
    - executa RESET
    - altera configurações
    - envia jobs PCL/PS
    - executa firmware

Ele envia somente comandos LPRINT previamente selecionados
para investigação de páginas internas da impressora.

COMANDOS JÁ INVESTIGADOS E NÃO REPETIDOS AQUI:

    LPRINTMENUS
    LPRINTTESTPAGE
    LPRINTDIRECTORY
    LPRINTPCLFONTS
    LPRINTPSFONTS
    LPRINTDIAG1TEST
    LPRINTDIAG2TEST
    LPRINTDIAG3TEST
"""

from __future__ import annotations

import socket
import time


# ============================================================
# CONFIGURAÇÃO
# ============================================================

RAW_PORT = 9100

CONNECT_TIMEOUT = 5.0

READ_TIMEOUT = 3.0

RETRIES = 3


# ============================================================
# COMANDOS
# ============================================================

COMMANDS = [

    (
        "LPRINTSTATUS",
        "@PJL LPRINTSTATUS",
        "Possível página/relatório de status."
    ),

    (
        "LPRINTINFO",
        "@PJL LPRINTINFO",
        "Possível página/relatório de informações."
    ),

    (
        "LPRINTCONFIG",
        "@PJL LPRINTCONFIG",
        "Possível página de configuração."
    ),

    (
        "LPRINTSUPPLIES",
        "@PJL LPRINTSUPPLIES",
        "Possível relatório de suprimentos."
    ),

    (
        "LPRINTDEVICE",
        "@PJL LPRINTDEVICE",
        "Possível relatório de informações do dispositivo."
    ),

    (
        "LPRINTFACTORY",
        "@PJL LPRINTFACTORY",
        "Possível relatório relacionado a fábrica."
    ),

    (
        "LPRINTNETWORK",
        "@PJL LPRINTNETWORK",
        "Possível página de configuração de rede."
    ),

    (
        "LPRINTMENU",
        "@PJL LPRINTMENU",
        "Variação singular de LPRINTMENUS."
    ),

    (
        "LPRINTTEST",
        "@PJL LPRINTTEST",
        "Variação genérica de teste."
    ),

    (
        "LPRINTDEMO",
        "@PJL LPRINTDEMO",
        "Possível página de demonstração."
    ),

    (
        "LPRINTDEMONSTRATION",
        "@PJL LPRINTDEMONSTRATION",
        "Possível página de demonstração."
    ),

]


# ============================================================
# ENVIO
# ============================================================

def send_pjl(
    ip: str,
    command: str,
) -> tuple[bool, str, float]:

    payload = (
        "\x1b%-12345X"
        "@PJL\n"
        f"{command}\n"
        "\x1b%-12345X"
    )

    started = time.perf_counter()

    last_error = ""

    for attempt in range(
        1,
        RETRIES + 1,
    ):

        try:

            print(
                f"Conectando em "
                f"{ip}:{RAW_PORT} "
                f"(tentativa "
                f"{attempt}/{RETRIES})..."
            )

            with socket.create_connection(
                (
                    ip,
                    RAW_PORT,
                ),
                timeout=CONNECT_TIMEOUT,
            ) as sock:

                print("Conectado.")

                sock.settimeout(
                    READ_TIMEOUT
                )

                sock.sendall(
                    payload.encode(
                        "latin-1",
                        errors="replace",
                    )
                )

                chunks: list[bytes] = []

                while True:

                    try:

                        data = sock.recv(
                            4096
                        )

                    except socket.timeout:

                        break

                    if not data:
                        break

                    chunks.append(
                        data
                    )

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

            return (
                True,
                response,
                elapsed,
            )

        except OSError as exc:

            last_error = str(exc)

            print(
                f"Falha: {exc}"
            )

            if attempt < RETRIES:

                time.sleep(0.5)

    elapsed = (
        time.perf_counter()
        - started
    )

    return (
        False,
        last_error,
        elapsed,
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "PRINTER ASSISTANT - MX611 EXTENDED LPRINT PROBE"
    )

    print("=" * 72)

    print()

    print(
        "Este teste investiga comandos LPRINT adicionais."
    )

    print()

    print(
        "NÃO executa:"
    )

    print(
        "  - SET"
    )

    print(
        "  - DEFAULT"
    )

    print(
        "  - RESET"
    )

    print(
        "  - firmware"
    )

    print(
        "  - jobs PCL/PS"
    )

    print()

    print(
        "Comandos de diagnóstico já conhecidos "
        "não serão repetidos."
    )

    print()

    ip = input(
        "Digite o IP da impressora [192.168.14.134]: "
    ).strip()

    if not ip:

        ip = "192.168.14.134"

    print()

    print(
        f"Impressora: {ip}"
    )

    print(
        f"RAW:        {RAW_PORT}"
    )

    print()

    print(
        "ATENÇÃO:"
    )

    print(
        "Alguns comandos LPRINT podem provocar "
        "impressão física."
    )

    print(
        "Observe a impressora após cada envio."
    )

    print()

    answer = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if answer != "S":

        print(
            "Teste cancelado."
        )

        return

    results = []

    for name, command, description in COMMANDS:

        print()

        print("=" * 72)

        print(
            f"TESTE: {name}"
        )

        print("=" * 72)

        print()

        print(
            f"Descrição : {description}"
        )

        print(
            f"Comando   : {command}"
        )

        print()

        print(
            "ATENÇÃO:"
        )

        print(
            "Este comando pode provocar "
            "atividade física na impressora."
        )

        print()

        answer = input(
            "Enviar este comando? [S/N/Q]: "
        ).strip().upper()

        if answer == "Q":

            print(
                "Teste interrompido."
            )

            break

        if answer != "S":

            print(
                "Comando ignorado."
            )

            results.append(
                (
                    name,
                    "IGNORADO",
                    0.0,
                    "",
                )
            )

            continue

        print()

        success, response, elapsed = send_pjl(
            ip,
            command,
        )

        print()

        if success:

            print(
                "Comando enviado."
            )

            print(
                f"Tempo: {elapsed:.3f}s"
            )

            status = "ENVIADO"

        else:

            print(
                "ERRO DE COMUNICAÇÃO."
            )

            print(
                response
            )

            print(
                f"Tempo: {elapsed:.3f}s"
            )

            status = "ERRO"

        print()

        print(
            "RESPOSTA PJL:"
        )

        print(
            "-" * 72
        )

        if response and success:

            print(
                response
            )

        else:

            print(
                "(sem resposta)"
            )

        print(
            "-" * 72
        )

        print()

        print(
            "Observe fisicamente a impressora."
        )

        print()

        print(
            "ANOTE:"
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
            "  4. Houve mensagem no painel?"
        )

        print(
            "  5. Houve erro?"
        )

        print(
            "  6. Não aconteceu nada?"
        )

        results.append(
            (
                name,
                status,
                elapsed,
                response,
            )
        )

        input(
            "\nPressione ENTER para continuar..."
        )

    print()

    print("=" * 72)

    print(
        "RESUMO"
    )

    print("=" * 72)

    print()

    for name, status, elapsed, response in results:

        print(
            f"{status:<10}"
            f"{name:<25}"
            f"{elapsed:>7.3f}s"
        )

    print()

    print(
        "IMPORTANTE:"
    )

    print(
        "ENVIADO não significa SUPORTADO."
    )

    print(
        "O efeito físico observado na impressora "
        "é o dado principal desta investigação."
    )

    print()

    print("=" * 72)


if __name__ == "__main__":

    main()