import socket
import time
from dataclasses import dataclass
from typing import Optional


RAW_PORT = 9100
CONNECT_TIMEOUT = 3.0
READ_TIMEOUT = 2.0
RETRIES = 3


@dataclass
class ProbeResult:
    variable: str
    inquire: Optional[str]
    dinquire: Optional[str]
    inquire_time: float
    dinquire_time: float


class PJLConnection:
    def __init__(self, host: str):
        self.host = host

    def _connect(self):
        last_error = None

        for attempt in range(1, RETRIES + 1):
            try:
                print(
                    f"Conectando em {self.host}:{RAW_PORT} "
                    f"(tentativa {attempt}/{RETRIES})..."
                )

                sock = socket.create_connection(
                    (self.host, RAW_PORT),
                    timeout=CONNECT_TIMEOUT,
                )

                sock.settimeout(READ_TIMEOUT)
                print("Conectado.")
                return sock

            except Exception as exc:
                last_error = exc

                if attempt < RETRIES:
                    time.sleep(0.3)

        raise last_error

    def request(self, command: str):
        sock = self._connect()

        try:
            payload = (
                "\x1b%-12345X"
                "@PJL\r\n"
                f"{command}\r\n"
                "\x1b%-12345X"
            ).encode("ascii", errors="replace")

            started = time.perf_counter()

            sock.sendall(payload)

            response = bytearray()

            while True:
                try:
                    chunk = sock.recv(4096)

                    if not chunk:
                        break

                    response.extend(chunk)

                except socket.timeout:
                    break

            elapsed = time.perf_counter() - started

            return response.decode(
                "latin-1",
                errors="replace",
            ), elapsed

        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass

            sock.close()

    def inquire(self, variable: str):
        return self.request(f"@PJL INQUIRE {variable}")

    def dinquire(self, variable: str):
        return self.request(f"@PJL DINQUIRE {variable}")


def clean_response(response: str) -> str:
    if not response:
        return ""

    text = response.replace("\x00", "")
    text = text.replace("\x1b%-12345X", "")
    text = text.replace("\x1bE", "")

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("@PJL"):
            continue

        lines.append(line)

    if not lines:
        return ""

    return " | ".join(lines)


def classify(value: Optional[str]) -> str:
    if value is None:
        return "SEM RESPOSTA"

    value = value.strip()

    if not value:
        return "SEM RESPOSTA"

    if value == '"?"':
        return "DESCONHECIDA / NÃO SUPORTADA"

    if value == "?":
        return "DESCONHECIDA / NÃO SUPORTADA"

    if value.startswith("@PJL"):
        return "RESPOSTA PJL NÃO PARSEADA"

    return "RESPOSTA"


def probe_variable(connection: PJLConnection, variable: str) -> ProbeResult:
    print()
    print("-" * 72)
    print(f"VARIÁVEL: {variable}")
    print("-" * 72)

    raw_inquire, inquire_time = connection.inquire(variable)
    inquire = clean_response(raw_inquire)

    print(f"INQUIRE  : {inquire or '(sem resposta)'}")
    print(f"TEMPO    : {inquire_time:.3f}s")

    raw_dinquire, dinquire_time = connection.dinquire(variable)
    dinquire = clean_response(raw_dinquire)

    print(f"DINQUIRE : {dinquire or '(sem resposta)'}")
    print(f"TEMPO    : {dinquire_time:.3f}s")

    print(f"STATUS   : {classify(inquire)}")

    return ProbeResult(
        variable=variable,
        inquire=inquire or None,
        dinquire=dinquire or None,
        inquire_time=inquire_time,
        dinquire_time=dinquire_time,
    )


def print_info_id(connection: PJLConnection):
    print()
    print("=" * 72)
    print("IDENTIDADE")
    print("=" * 72)

    response, elapsed = connection.request("@PJL INFO ID")
    cleaned = clean_response(response)

    print(f"RESPOSTA : {cleaned or '(sem resposta)'}")
    print(f"TEMPO    : {elapsed:.3f}s")


def print_info_config(connection: PJLConnection):
    print()
    print("=" * 72)
    print("INFO CONFIG")
    print("=" * 72)

    response, elapsed = connection.request("@PJL INFO CONFIG")

    if response:
        print(response.rstrip())
    else:
        print("(sem resposta)")

    print(f"TEMPO    : {elapsed:.3f}s")


def print_summary(results):
    print()
    print()
    print("=" * 72)
    print("RESUMO DA DESCOBERTA")
    print("=" * 72)

    supported = []
    unknown = []
    no_response = []

    for result in results:
        value = result.inquire

        if not value:
            no_response.append(result.variable)
        elif value in ('?', '"?"'):
            unknown.append(result.variable)
        elif value.startswith("@PJL"):
            unknown.append(result.variable)
        else:
            supported.append(result.variable)

    print()
    print("VARIÁVEIS COM RESPOSTA ÚTIL")
    print("-" * 72)

    for variable in supported:
        result = next(
            item for item in results
            if item.variable == variable
        )

        print(
            f"{variable:<18} "
            f"CURRENT={result.inquire!r:<18} "
            f"DEFAULT={result.dinquire!r}"
        )

    print()
    print("VARIÁVEIS DESCONHECIDAS / NÃO SUPORTADAS")
    print("-" * 72)

    for variable in unknown:
        print(variable)

    print()
    print("VARIÁVEIS SEM RESPOSTA")
    print("-" * 72)

    for variable in no_response:
        print(variable)

    print()
    print("=" * 72)
    print("FIM DA DESCOBERTA")
    print("=" * 72)


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 SYSTEM CAPABILITY PROBE")
    print("=" * 72)

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
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
    print("Serão somente consultadas variáveis PJL.")
    print()

    confirm = input("Continuar? [S/N]: ").strip().upper()

    if confirm != "S":
        print("Teste cancelado.")
        return

    connection = PJLConnection(ip)

    print_info_id(connection)
    print_info_config(connection)

    variables = [
        # Impressão
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

        # Idioma / região
        "LANG",
        "LANGUAGE",
        "TIMEZONE",
        "COUNTRY",
        "COUNTRYCODE",

        # Job
        "JOBNAME",
        "USERNAME",
        "USTATUS",

        # Sistema
        "DISPLAY",
        "SERIALNUMBER",
        "FIRMWARE",

        # Scanner
        "SCANNER",
        "SCANNERFIRMWARE",
        "SCANNERBOOTFIRMWARE",
        "SCANNERDUPLEX",
        "SCANNERDUPLEXFIRMWARE",

        # Cópia
        "COPY",
        "COPIES",
        "COPYDUPLEX",
        "COPYORIGINAL",
        "COPYOUTPUT",
        "COPYCOLLATE",
        "COPYQUALITY",
        "COPYDENSITY",
        "COPYCONTRAST",
        "COPYDARKNESS",
        "COPYPAPER",

        # Digitalização
        "SCAN",
        "SCANRESOLUTION",
        "SCANDUPLEX",
        "SCANMODE",
        "SCANFORMAT",
        "SCANDESTINATION",
        "SCANQUALITY",
        "SCANCOLOR",

        # Energia / comportamento
        "POWERSAVE",
        "SLEEP",
        "SLEEPDELAY",
        "AUTOOFF",
        "WAKEUP",

        # Rede
        "NETWORK",
        "IPADDRESS",
        "SUBNET",
        "GATEWAY",
        "DHCP",
        "HOSTNAME",

        # Estado
        "STATUS",
        "DEVICE",
        "PAGECOUNT",
        "TOTALPAGES",
        "LIFETIMEPAGES",
    ]

    results = []

    print()
    print("=" * 72)
    print("CONSULTAS PJL")
    print("=" * 72)

    for variable in variables:
        try:
            result = probe_variable(connection, variable)
            results.append(result)

        except Exception as exc:
            print(f"ERRO AO CONSULTAR {variable}: {exc}")

            results.append(
                ProbeResult(
                    variable=variable,
                    inquire=None,
                    dinquire=None,
                    inquire_time=0.0,
                    dinquire_time=0.0,
                )
            )

    print_summary(results)

    print()
    print("Nenhuma configuracao foi alterada.")
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum job foi enviado.")
    print()
    print("Os resultados devem ser usados para descobrir")
    print("quais variáveis realmente existem na MX611.")
    print()


if __name__ == "__main__":
    main()