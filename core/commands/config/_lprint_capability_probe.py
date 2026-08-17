"""
PRINTER ASSISTANT
MX611 LPRINT CAPABILITY PROBE

Descobre quais comandos LPRINT de páginas internas
são realmente executados pela impressora.

IMPORTANTE:

- Não executa DEFAULT.
- Não executa SET.
- Não executa RESET.
- Não altera configurações.
- Não envia job PCL/PS.
- Apenas envia comandos LPRINT explicitamente definidos
  neste teste.
- O resultado físico da página deve ser observado pelo operador.

Comandos já confirmados anteriormente:

    @PJL LPRINTMENUS
    @PJL LPRINTTESTPAGE

Comandos investigados neste probe:

    @PJL LPRINTDIRECTORY
    @PJL LPRINTPCLFONTS
    @PJL LPRINTPSFONTS
    @PJL LPRINTDIAG1TEST
    @PJL LPRINTDIAG2TEST
    @PJL LPRINTDIAG3TEST
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass


# ============================================================
# CONFIGURAÇÃO
# ============================================================

RAW_PORT = 9100

CONNECT_TIMEOUT = 5.0

READ_TIMEOUT = 2.0

RETRIES = 3


# ============================================================
# IMPRESSORA
# ============================================================

PRINTER_DEFAULT_IP = "192.168.14.134"


# ============================================================
# COMANDOS
# ============================================================

COMMANDS = [
    {
        "name": "LPRINTDIRECTORY",
        "command": "@PJL LPRINTDIRECTORY",
        "description": (
            "Lista diretórios de flash/disco."
        ),
    },
    {
        "name": "LPRINTPCLFONTS",
        "command": "@PJL LPRINTPCLFONTS",
        "description": (
            "Lista fontes PCL."
        ),
    },
    {
        "name": "LPRINTPSFONTS",
        "command": "@PJL LPRINTPSFONTS",
        "description": (
            "Lista fontes PostScript."
        ),
    },
    {
        "name": "LPRINTDIAG1TEST",
        "command": "@PJL LPRINTDIAG1TEST",
        "description": (
            "Teste diagnóstico 1."
        ),
    },
    {
        "name": "LPRINTDIAG2TEST",
        "command": "@PJL LPRINTDIAG2TEST",
        "description": (
            "Teste diagnóstico 2."
        ),
    },
    {
        "name": "LPRINTDIAG3TEST",
        "command": "@PJL LPRINTDIAG3TEST",
        "description": (
            "Teste diagnóstico 3."
        ),
    },
]


# ============================================================
# RESULTADO
# ============================================================


@dataclass
class ProbeResult:

    name: str

    command: str

    description: str

    success: bool = False

    response: str = ""

    elapsed: float = 0.0

    error: str = ""


# ============================================================
# CLIENTE RAW
# ============================================================


class PJLClient:

    def __init__(
        self,
        ip: str,
        port: int = RAW_PORT,
    ):

        self.ip = ip

        self.port = port

    # ========================================================
    # ENVIO
    # ========================================================

    def send(
        self,
        command: str,
    ) -> tuple[str, float]:

        payload = (
            "\x1b%-12345X"
            "@PJL\r\n"
            f"{command}\r\n"
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
                    f"{self.ip}:{self.port} "
                    f"(tentativa "
                    f"{attempt}/{RETRIES})..."
                )

                with socket.create_connection(
                    (
                        self.ip,
                        self.port,
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

                        chunks.append(data)

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

                return response, elapsed

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

        raise RuntimeError(
            (
                "Falha ao comunicar com "
                f"{self.ip}:{self.port}: "
                f"{last_error}"
            )
        )


# ============================================================
# LIMPEZA DA RESPOSTA
# ============================================================


def clean_response(
    response: str,
) -> str:

    if not response:

        return ""

    response = response.replace(
        "\x1b%-12345X",
        "",
    )

    response = response.replace(
        "\x00",
        "",
    )

    return response.strip()


# ============================================================
# TESTE INDIVIDUAL
# ============================================================


def test_command(
    client: PJLClient,
    item: dict,
) -> ProbeResult:

    result = ProbeResult(
        name=item["name"],
        command=item["command"],
        description=item["description"],
    )

    print()
    print("=" * 72)
    print(
        f"TESTE: {item['name']}"
    )
    print("=" * 72)

    print()

    print(
        f"Descrição : {item['description']}"
    )

    print(
        f"Comando   : {item['command']}"
    )

    print()

    print(
        "ATENÇÃO:"
    )

    print(
        "Este comando pode provocar impressão "
        "ou atividade física na impressora."
    )

    print(
        "Observe a impressora após o envio."
    )

    print()

    try:

        response, elapsed = client.send(
            item["command"]
        )

        result.success = True

        result.response = clean_response(
            response
        )

        result.elapsed = elapsed

        print()

        print(
            "Comando enviado."
        )

        print(
            f"Tempo: {elapsed:.3f}s"
        )

        print()

        if result.response:

            print(
                "RESPOSTA PJL:"
            )

            print(
                "-" * 72
            )

            print(
                result.response
            )

            print(
                "-" * 72
            )

        else:

            print(
                "RESPOSTA PJL: (sem resposta)"
            )

    except Exception as exc:

        result.error = str(exc)

        print()

        print(
            f"ERRO: {exc}"
        )

    return result


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    print("=" * 72)

    print(
        "PRINTER ASSISTANT - MX611 LPRINT "
        "CAPABILITY PROBE"
    )

    print("=" * 72)

    print()

    print(
        "Este teste investiga comandos LPRINT "
        "de páginas internas."
    )

    print()

    print(
        "NÃO executa:"
    )

    print(
        "  - DEFAULT"
    )

    print(
        "  - SET"
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
        "Já confirmados:"
    )

    print(
        "  ✓ @PJL LPRINTMENUS"
    )

    print(
        "  ✓ @PJL LPRINTTESTPAGE"
    )

    print()

    print(
        "Serão investigados:"
    )

    for item in COMMANDS:

        print(
            f"  ? {item['command']}"
        )

    print()

    ip = input(
        f"Digite o IP da impressora "
        f"[{PRINTER_DEFAULT_IP}]: "
    ).strip()

    if not ip:

        ip = PRINTER_DEFAULT_IP

    print()

    print(
        f"Impressora: {ip}"
    )

    print(
        f"RAW:        {RAW_PORT}"
    )

    print()

    confirm = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirm != "S":

        print(
            "Teste cancelado."
        )

        return

    client = PJLClient(
        ip=ip,
        port=RAW_PORT,
    )

    resultados: list[ProbeResult] = []

    for item in COMMANDS:

        resultado = test_command(
            client,
            item,
        )

        resultados.append(
            resultado
        )

        print()

        print(
            "Observe fisicamente a impressora."
        )

        print()

        input(
            "Pressione ENTER para continuar..."
        )

    # ========================================================
    # RESUMO
    # ========================================================

    print()
    print("=" * 72)
    print("RESUMO DA DESCOBERTA")
    print("=" * 72)

    print()

    for resultado in resultados:

        if resultado.success:

            status = "ENVIADO"

        else:

            status = "ERRO"

        print(
            f"{status:<10} "
            f"{resultado.name:<20} "
            f"{resultado.elapsed:.3f}s"
        )

        if resultado.error:

            print(
                f"           ERRO: "
                f"{resultado.error}"
            )

    print()

    print("=" * 72)
    print("INTERPRETAÇÃO")
    print("=" * 72)

    print()

    print(
        "IMPORTANTE:"
    )

    print(
        "ENVIADO não significa SUPORTADO."
    )

    print(
        "O operador deve registrar o que "
        "aconteceu fisicamente."
    )

    print()

    print(
        "Para cada comando, anote:"
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

    print()

    print(
        "Nenhuma configuração foi alterada "
        "por este programa."
    )

    print()

    print("=" * 72)


if __name__ == "__main__":

    main()