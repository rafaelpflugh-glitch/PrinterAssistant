import socket
import time
from dataclasses import dataclass
from typing import Optional


HOST = "192.168.14.134"
PORT = 9100

CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 4.0
RETRIES = 3


@dataclass
class PJLResult:
    command: str
    response: Optional[str]
    elapsed: float
    error: Optional[str] = None


class PJLClient:
    def __init__(self, host: str, port: int = 9100):
        self.host = host
        self.port = port

    def _connect(self) -> socket.socket:
        last_error = None

        for attempt in range(1, RETRIES + 1):
            print(
                f"Conectando em {self.host}:{self.port} "
                f"(tentativa {attempt}/{RETRIES})..."
            )

            try:
                sock = socket.create_connection(
                    (self.host, self.port),
                    timeout=CONNECT_TIMEOUT,
                )
                sock.settimeout(READ_TIMEOUT)
                return sock

            except Exception as exc:
                last_error = exc

                if attempt < RETRIES:
                    time.sleep(0.5)

        raise last_error

    def command(self, command: str) -> PJLResult:
        started = time.perf_counter()

        try:
            sock = self._connect()

            try:
                payload = command.encode("ascii", errors="replace")
                sock.sendall(payload)

                data = bytearray()

                while True:
                    try:
                        chunk = sock.recv(4096)
                    except socket.timeout:
                        break

                    if not chunk:
                        break

                    data.extend(chunk)

                    if b"\x0c" in chunk:
                        break

                response = data.decode(
                    "latin-1",
                    errors="replace",
                ).strip()

            finally:
                sock.close()

            elapsed = time.perf_counter() - started

            return PJLResult(
                command=command,
                response=response or None,
                elapsed=elapsed,
            )

        except Exception as exc:
            elapsed = time.perf_counter() - started

            return PJLResult(
                command=command,
                response=None,
                elapsed=elapsed,
                error=str(exc),
            )


def clean_response(response: Optional[str]) -> Optional[str]:
    if response is None:
        return None

    text = response.strip()

    if text.startswith("@PJL"):
        lines = text.splitlines()

        useful = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if line.startswith("@PJL"):
                continue

            useful.append(line)

        if useful:
            return useful[-1]

    return text


def inquire(client: PJLClient, variable: str) -> PJLResult:
    return client.command(
        f"\x1b%-12345X@PJL INQUIRE {variable}\r\n"
        f"\x1b%-12345X"
    )


def dinquire(client: PJLClient, variable: str) -> PJLResult:
    return client.command(
        f"\x1b%-12345X@PJL DINQUIRE {variable}\r\n"
        f"\x1b%-12345X"
    )


def info_id(client: PJLClient) -> PJLResult:
    return client.command(
        "\x1b%-12345X@PJL INFO ID\r\n"
        "\x1b%-12345X"
    )


def info_config(client: PJLClient) -> PJLResult:
    return client.command(
        "\x1b%-12345X@PJL INFO CONFIG\r\n"
        "\x1b%-12345X"
    )


def print_result(label: str, result: PJLResult) -> None:
    value = clean_response(result.response)

    print(f"{label:<12}: {value}")

    if result.error:
        print(f"{'ERRO':<12}: {result.error}")

    print(f"{'Tempo':<12}: {result.elapsed:.3f}s")


def main() -> None:
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 SCANNER / ADF CAPABILITY PROBE")
    print("=" * 72)
    print()

    ip = input(f"Digite o IP da impressora [{HOST}]: ").strip()

    host = ip if ip else HOST

    client = PJLClient(host, PORT)

    print()
    print(f"Impressora: {host}")
    print(f"RAW:        {PORT}")
    print()

    print("Este teste:")
    print()
    print("- NAO executa SET.")
    print("- NAO executa DEFAULT.")
    print("- NAO executa RESET.")
    print("- NAO envia jobs.")
    print("- NAO imprime nenhuma pagina.")
    print("- NAO altera configuracoes.")
    print()
    print("Serão somente consultadas informações PJL relacionadas")
    print("ao dispositivo, scanner, ADF e recursos disponíveis.")
    print()

    answer = input("Continuar? [S/N]: ").strip().upper()

    if answer != "S":
        print()
        print("Teste cancelado.")
        return

    print()
    print("=" * 72)
    print("1. IDENTIDADE")
    print("=" * 72)

    result = info_id(client)

    if result.error:
        print(f"ERRO: {result.error}")
    else:
        print(result.response or "(sem resposta)")

    print()
    print("=" * 72)
    print("2. INFO CONFIG")
    print("=" * 72)

    result = info_config(client)

    if result.error:
        print(f"ERRO: {result.error}")
    else:
        print(result.response or "(sem resposta)")

    print()
    print("=" * 72)
    print("3. VARIAVEIS RELACIONADAS AO SCANNER / ADF")
    print("=" * 72)
    print()

    variables = [
        "SCANNER",
        "ADF",
        "SCANNERDUPLEX",
        "DUPLEX",
        "COPIES",
        "PAPER",
        "PAPERLENGTH",
        "PAPERWIDTH",
        "MEDIATYPE",
        "RESOLUTION",
        "ORIENTATION",
        "USTATUS",
        "LANGUAGE",
        "LANG",
    ]

    results = []

    for variable in variables:
        print("-" * 72)
        print(f"VARIAVEL: {variable}")
        print("-" * 72)

        print()

        inq = inquire(client, variable)
        dinq = dinquire(client, variable)

        current = clean_response(inq.response)
        default = clean_response(dinq.response)

        print_result("INQUIRE", inq)
        print_result("DINQUIRE", dinq)

        results.append(
            {
                "variable": variable,
                "current": current,
                "default": default,
                "inq_error": inq.error,
                "dinq_error": dinq.error,
            }
        )

        print()

    print("=" * 72)
    print("4. RESUMO")
    print("=" * 72)
    print()

    print(
        f"{'VARIAVEL':<18}"
        f"{'CURRENT':<24}"
        f"{'DEFAULT':<24}"
    )

    print("-" * 66)

    for item in results:
        variable = item["variable"]
        current = item["current"]
        default = item["default"]

        current_text = str(current) if current is not None else "NONE"
        default_text = str(default) if default is not None else "NONE"

        print(
            f"{variable:<18}"
            f"{current_text:<24}"
            f"{default_text:<24}"
        )

    print()
    print("=" * 72)
    print("5. INTERPRETACAO")
    print("=" * 72)
    print()

    print(
        "Valores diferentes de '?' ou NONE devem ser tratados "
        "como candidatos a variaveis suportadas."
    )

    print(
        "Uma variavel retornando '?' nao deve ser considerada "
        "confirmada apenas por aparecer em uma consulta."
    )

    print(
        "Nenhuma variavel foi modificada neste teste."
    )

    print(
        "Nenhum DEFAULT foi alterado."
    )

    print(
        "Nenhum RESET foi executado."
    )

    print(
        "Nenhum job foi enviado."
    )

    print()
    print("=" * 72)
    print("FIM")
    print("=" * 72)


if __name__ == "__main__":
    main()