"""
Printer Assistant - PJL Variable Discovery Probe

Descobre sistematicamente quais variáveis PJL são reconhecidas
pela Lexmark MX611/MX611dhe.

IMPORTANTE:
- Somente leitura.
- Não executa SET.
- Não executa DEFAULT.
- Não executa RESET.
- Não envia jobs.
- Não altera configurações.

O teste consulta INQUIRE e DINQUIRE para um conjunto de
variáveis documentadas pela Lexmark e algumas variáveis
relacionadas já observadas na MX611.

Resultado:
- SUPORTADA: respondeu com valor diferente de "?"
- DESCONHECIDA: respondeu "?"
- SEM RESPOSTA: não houve resposta dentro do timeout
- ECO/NAO INTERPRETADA: a resposta não correspondeu ao
  formato esperado
"""

import socket
import time


RAW_PORT = 9100

CONNECT_TIMEOUT = 3.0
READ_TIMEOUT = 1.5
RETRIES = 3


# ---------------------------------------------------------------------------
# Variáveis documentadas / relevantes para a família MX610/MX611
# ---------------------------------------------------------------------------

VARIABLES = [
    # Ambiente geral
    "AUTOCONT",
    "BINDING",
    "BITSPERPIXEL",
    "CLEARABLEWARNINGS",
    "COPIES",
    "CPLOCK",
    "DENSITY",
    "DUPLEX",
    "ECONOMODE",
    "FORMATTERNUMBER",
    "FORMLINES",
    "HELDJOBTIMEOUT",
    "HOLD",
    "HOLDKEY",
    "HOLDTYPE",

    # Bandejas / papel
    "INTRAY1",
    "INTRAY2",
    "INTRAY3",
    "INTRAY4",
    "INTRAY5",
    "INTRAY1SIZE",
    "INTRAY2SIZE",
    "INTRAY3SIZE",
    "INTRAY4SIZE",
    "INTRAY5SIZE",

    "LANG",
    "LOWTONER",
    "MANUALFEED",
    "MEDIATYPE",
    "MPTRAY",
    "ORIENTATION",
    "OUTBIN",
    "PAGEPROTECT",
    "PAPER",

    # Linguagem / processamento
    "PASSWORD",
    "PERSONALITY",
    "POWERSAVE",
    "POWERSAVETIME",
    "QTY",
    "REPEATJOBTIMEOUT",
    "REPRINT",
    "RESERVEJOBTIMEOUT",
    "RESOLUTION",
    "RESOURCESAVE",
    "STRINGCODESET",
    "TIMEOUT",
    "USERNAME",
    "VERIFYJOBTIMEOUT",
    "WIDEA4",

    # Variáveis já observadas durante os testes
    "MEDIAWEIGHT",
    "MEDIATEXTURE",
    "MEDIASOURCE",
    "TRAY",
    "INPUTTRAY",
    "OUTPUTBIN",
    "LANGUAGE",
    "TIMEZONE",
    "COUNTRY",
    "COUNTRYCODE",
    "JOBNAME",
    "USTATUS",
    "DISPLAY",
    "SERIALNUMBER",
    "FIRMWARE",
]


# ---------------------------------------------------------------------------
# Comunicação RAW/PJL
# ---------------------------------------------------------------------------

def connect(ip):
    last_error = None

    for attempt in range(1, RETRIES + 1):
        try:
            print(
                f"Conectando em {ip}:{RAW_PORT} "
                f"(tentativa {attempt}/{RETRIES})..."
            )

            sock = socket.create_connection(
                (ip, RAW_PORT),
                timeout=CONNECT_TIMEOUT,
            )

            sock.settimeout(READ_TIMEOUT)

            print("Conectado.")
            return sock

        except OSError as exc:
            last_error = exc

            if attempt < RETRIES:
                time.sleep(0.25)

    raise ConnectionError(
        f"Não foi possível conectar em {ip}:{RAW_PORT}: {last_error}"
    )


def read_response(sock):
    chunks = []

    while True:
        try:
            data = sock.recv(4096)

            if not data:
                break

            chunks.append(data)

            if b"\x0c" in data:
                break

        except socket.timeout:
            break

    return b"".join(chunks)


def send_pjl(ip, command):
    payload = (
        b"\x1b%-12345X"
        + command.encode("ascii", errors="replace")
        + b"\r\n"
    )

    start = time.perf_counter()

    sock = connect(ip)

    try:
        sock.sendall(payload)
        response = read_response(sock)
    finally:
        sock.close()

    elapsed = time.perf_counter() - start

    return response, elapsed


# ---------------------------------------------------------------------------
# Normalização das respostas
# ---------------------------------------------------------------------------

def clean_response(response):
    if not response:
        return None

    text = response.decode(
        "latin-1",
        errors="replace",
    )

    text = text.replace("\x0c", "")
    text = text.replace("\x1b", "")
    text = text.replace("\x00", "")

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    return lines[-1]


def classify(value):
    if value is None:
        return "SEM RESPOSTA"

    stripped = value.strip()

    if stripped == '"?"':
        return "DESCONHECIDA"

    if stripped == "?":
        return "DESCONHECIDA"

    if stripped.startswith("@PJL"):
        return "ECO/NAO INTERPRETADA"

    return "SUPORTADA"


# ---------------------------------------------------------------------------
# Consulta de uma variável
# ---------------------------------------------------------------------------

def inquire(ip, variable, default=False):
    command = (
        f"@PJL DINQUIRE {variable}"
        if default
        else f"@PJL INQUIRE {variable}"
    )

    response, elapsed = send_pjl(ip, command)

    value = clean_response(response)

    return value, elapsed


def test_variable(ip, variable):
    print()
    print("-" * 72)
    print(f"VARIAVEL: {variable}")
    print("-" * 72)

    try:
        current, current_time = inquire(
            ip,
            variable,
            default=False,
        )

        print(f"INQUIRE  : {current}")
        print(f"Tempo    : {current_time:.3f}s")

    except Exception as exc:
        print(f"INQUIRE  : ERRO - {exc}")
        current = None
        current_time = 0.0

    try:
        default, default_time = inquire(
            ip,
            variable,
            default=True,
        )

        print(f"DINQUIRE : {default}")
        print(f"Tempo    : {default_time:.3f}s")

    except Exception as exc:
        print(f"DINQUIRE : ERRO - {exc}")
        default = None
        default_time = 0.0

    current_class = classify(current)
    default_class = classify(default)

    if current_class == "SUPORTADA":
        current_result = "SUPORTADA"
    else:
        current_result = current_class

    if default_class == "SUPORTADA":
        default_result = "SUPORTADA"
    else:
        default_result = default_class

    print()
    print(f"CURRENT RESULT : {current_result}")
    print(f"DEFAULT RESULT : {default_result}")

    return {
        "variable": variable,
        "current": current,
        "default": default,
        "current_result": current_result,
        "default_result": default_result,
        "current_time": current_time,
        "default_time": default_time,
    }


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------

def print_report(results):
    supported = []
    unknown = []
    no_response = []
    uninterpreted = []

    for result in results:
        variable = result["variable"]

        current_result = result["current_result"]
        default_result = result["default_result"]

        if (
            current_result == "SUPORTADA"
            or default_result == "SUPORTADA"
        ):
            supported.append(result)
            continue

        if (
            current_result == "DESCONHECIDA"
            and default_result == "DESCONHECIDA"
        ):
            unknown.append(result)
            continue

        if (
            current_result == "SEM RESPOSTA"
            and default_result == "SEM RESPOSTA"
        ):
            no_response.append(result)
            continue

        uninterpreted.append(result)

    print()
    print("=" * 72)
    print("RESULTADO DA DESCOBERTA PJL")
    print("=" * 72)

    print()
    print(f"VARIAVEIS TESTADAS : {len(results)}")
    print(f"SUPORTADAS         : {len(supported)}")
    print(f"DESCONHECIDAS      : {len(unknown)}")
    print(f"SEM RESPOSTA       : {len(no_response)}")
    print(f"NAO INTERPRETADAS  : {len(uninterpreted)}")

    print()
    print("=" * 72)
    print("VARIAVEIS SUPORTADAS")
    print("=" * 72)

    for result in supported:
        print(
            f"{result['variable']:<24} "
            f"CURRENT={str(result['current']):<18} "
            f"DEFAULT={result['default']}"
        )

    print()
    print("=" * 72)
    print("VARIAVEIS DESCONHECIDAS")
    print("=" * 72)

    for result in unknown:
        print(result["variable"])

    print()
    print("=" * 72)
    print("SEM RESPOSTA")
    print("=" * 72)

    for result in no_response:
        print(result["variable"])

    print()
    print("=" * 72)
    print("RESPOSTAS NAO INTERPRETADAS")
    print("=" * 72)

    for result in uninterpreted:
        print(
            f"{result['variable']}: "
            f"CURRENT={result['current']} "
            f"DEFAULT={result['default']}"
        )

    print()
    print("=" * 72)
    print("FIM DA DESCOBERTA")
    print("=" * 72)

    print()
    print("Nenhuma configuração foi alterada.")
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum job foi enviado.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL VARIABLE DISCOVERY PROBE")
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
    print("Serão somente consultadas variaveis PJL.")
    print()

    answer = input("Continuar? [S/N]: ").strip().upper()

    if answer != "S":
        print("Teste cancelado.")
        return

    print()
    print("=" * 72)
    print("INICIANDO DESCOBERTA")
    print("=" * 72)

    results = []

    for variable in VARIABLES:
        try:
            result = test_variable(
                ip,
                variable,
            )

            results.append(result)

        except Exception as exc:
            print()
            print(f"Falha ao testar {variable}: {exc}")

            results.append(
                {
                    "variable": variable,
                    "current": None,
                    "default": None,
                    "current_result": "SEM RESPOSTA",
                    "default_result": "SEM RESPOSTA",
                    "current_time": 0.0,
                    "default_time": 0.0,
                }
            )

    print_report(results)


if __name__ == "__main__":
    main()