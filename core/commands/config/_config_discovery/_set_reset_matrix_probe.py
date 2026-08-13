import socket
import time


HOST = "192.168.14.134"
PORT = 9100

CONNECT_TIMEOUT = 3.0
READ_TIMEOUT = 3.0
RETRIES = 3


# ============================================================
# VARIÁVEIS REAIS DESCOBERTAS EM @PJL INFO VARIABLES
#
# IMPORTANTE:
# - SET será usado somente no ambiente corrente.
# - DEFAULT nunca será executado.
# - RESET será usado ao final de cada teste.
# - Nenhum job será enviado.
# ============================================================

TESTS = [
    {
        "name": "DUPLEX",
        "values": ["ON", "OFF"],
    },
    {
        "name": "RESOLUTION",
        "values": ["300", "1200"],
    },
    {
        "name": "ORIENTATION",
        "values": ["LANDSCAPE", "PORTRAIT"],
    },
    {
        "name": "DENSITY",
        "values": ["1", "5"],
    },
    {
        "name": "ECONOMODE",
        "values": ["ON", "OFF"],
    },
    {
        "name": "POWERSAVE",
        "values": ["OFF", "ON"],
    },
    {
        "name": "POWERSAVETIME",
        "values": ["0", "240"],
    },
    {
        "name": "TIMEOUT",
        "values": ["0", "255"],
    },
    {
        "name": "REPRINT",
        "values": ["ON", "OFF", "AUTO"],
    },
    {
        "name": "RESOURCESAVE",
        "values": ["ON", "AUTO"],
    },
    {
        "name": "PAGEPROTECT",
        "values": ["ON", "AUTO"],
    },
    {
        "name": "MPTRAY",
        "values": ["MANUAL", "FIRST", "CASSETTE"],
    },
    {
        "name": "BINDING",
        "values": ["SHORTEDGE", "LONGEDGE"],
    },
    {
        "name": "AUTOCONT",
        "values": ["0", "255"],
    },
    {
        "name": "FORMLINES",
        "values": ["1", "255"],
    },
    {
        "name": "STRINGCODESET",
        "values": ["UTF8", "PC858"],
    },
]


def connect():
    last_error = None

    for attempt in range(1, RETRIES + 1):
        print(
            f"Conectando em {HOST}:{PORT} "
            f"(tentativa {attempt}/{RETRIES})..."
        )

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CONNECT_TIMEOUT)

        try:
            sock.connect((HOST, PORT))
            sock.settimeout(READ_TIMEOUT)
            return sock

        except Exception as exc:
            last_error = exc
            sock.close()
            time.sleep(0.2)

    raise ConnectionError(
        f"Não foi possível conectar em {HOST}:{PORT}: {last_error}"
    )


def send_pjl(command, read_response=True):
    sock = connect()

    try:
        payload = command.encode("latin-1", errors="replace")

        sock.sendall(payload)

        if not read_response:
            return ""

        chunks = []

        while True:
            try:
                data = sock.recv(4096)

                if not data:
                    break

                chunks.append(data)

            except socket.timeout:
                break

        raw = b"".join(chunks)

        return raw.decode("latin-1", errors="replace")

    finally:
        sock.close()


def clean_response(response):
    if response is None:
        return ""

    text = response.replace("\x00", "").strip()

    return text


def inquire(variable):
    command = (
        "\x1b%-12345X"
        "@PJL INQUIRE "
        + variable
        + "\r\n"
        "\x1b%-12345X"
    )

    response = send_pjl(command)
    response = clean_response(response)

    # Remove ecos da própria consulta quando a impressora
    # devolve o comando em vez do valor.
    lines = [
        line.strip()
        for line in response.splitlines()
        if line.strip()
    ]

    filtered = []

    for line in lines:
        upper = line.upper()

        if upper.startswith("@PJL INQUIRE"):
            continue

        if upper.startswith("@PJL DINQUIRE"):
            continue

        if upper == variable.upper():
            continue

        filtered.append(line)

    if not filtered:
        return ""

    return filtered[-1]


def dinquire(variable):
    command = (
        "\x1b%-12345X"
        "@PJL DINQUIRE "
        + variable
        + "\r\n"
        "\x1b%-12345X"
    )

    response = send_pjl(command)
    response = clean_response(response)

    lines = [
        line.strip()
        for line in response.splitlines()
        if line.strip()
    ]

    filtered = []

    for line in lines:
        upper = line.upper()

        if upper.startswith("@PJL INQUIRE"):
            continue

        if upper.startswith("@PJL DINQUIRE"):
            continue

        if upper == variable.upper():
            continue

        filtered.append(line)

    if not filtered:
        return ""

    return filtered[-1]


def set_variable(variable, value):
    command = (
        "\x1b%-12345X"
        f"@PJL SET {variable}={value}\r\n"
        "\x1b%-12345X"
    )

    send_pjl(command, read_response=False)


def reset():
    command = (
        "\x1b%-12345X"
        "@PJL RESET\r\n"
        "\x1b%-12345X"
    )

    send_pjl(command, read_response=False)


def print_state(variable):
    current = inquire(variable)
    default = dinquire(variable)

    print(f"INQUIRE  : {current or '(sem resposta)'}")
    print(f"DINQUIRE : {default or '(sem resposta)'}")

    return current, default


def test_variable(variable, values):
    print()
    print("=" * 72)
    print(f"VARIÁVEL: {variable}")
    print("=" * 72)

    print()
    print("1. ESTADO ORIGINAL")
    print("-" * 72)

    original_current, original_default = print_state(variable)

    print()
    print(f"CURRENT ORIGINAL : {original_current or '(sem resposta)'}")
    print(f"DEFAULT ORIGINAL : {original_default or '(sem resposta)'}")

    if not original_default:
        print()
        print("⚠ DEFAULT sem resposta.")
        print("Variável não será testada.")
        return

    results = []

    for value in values:
        print()
        print("=" * 72)
        print(f"2. TESTE SET {variable}={value}")
        print("=" * 72)

        print()
        print(f"@PJL SET {variable}={value}")

        try:
            set_variable(variable, value)

            time.sleep(0.5)

            current_after_set = inquire(variable)
            default_after_set = dinquire(variable)

            print()
            print("Estado após SET:")
            print(f"INQUIRE  : {current_after_set or '(sem resposta)'}")
            print(f"DINQUIRE : {default_after_set or '(sem resposta)'}")

            current_ok = (
                current_after_set.upper() == value.upper()
            )

            default_ok = (
                default_after_set.upper()
                == original_default.upper()
            )

            if current_ok:
                print(
                    f"✓ SET {variable}={value} "
                    "alterou o ambiente corrente."
                )
            else:
                print(
                    f"✗ SET {variable}={value} "
                    "não produziu o valor esperado."
                )

            if default_ok:
                print(
                    "✓ DEFAULT permaneceu inalterado."
                )
            else:
                print(
                    "!!! ATENÇÃO: DEFAULT mudou !!!"
                )

            results.append(
                {
                    "value": value,
                    "set_ok": current_ok,
                    "default_ok": default_ok,
                    "current": current_after_set,
                    "default": default_after_set,
                }
            )

        except Exception as exc:
            print()
            print(f"✗ ERRO durante SET: {exc}")

            results.append(
                {
                    "value": value,
                    "set_ok": False,
                    "default_ok": False,
                    "current": "",
                    "default": "",
                    "error": str(exc),
                }
            )

        print()
        print("3. RESET")
        print("-" * 72)

        try:
            reset()

            time.sleep(0.5)

            current_after_reset = inquire(variable)
            default_after_reset = dinquire(variable)

            print()
            print("Estado após RESET:")
            print(
                f"INQUIRE  : "
                f"{current_after_reset or '(sem resposta)'}"
            )
            print(
                f"DINQUIRE : "
                f"{default_after_reset or '(sem resposta)'}"
            )

            reset_current_ok = (
                current_after_reset.upper()
                == original_current.upper()
            )

            reset_default_ok = (
                default_after_reset.upper()
                == original_default.upper()
            )

            if reset_current_ok:
                print(
                    "✓ RESET devolveu o ambiente "
                    "ao estado original."
                )
            else:
                print(
                    "✗ RESET NÃO devolveu "
                    "o estado original."
                )

            if reset_default_ok:
                print(
                    "✓ DEFAULT continua preservado."
                )
            else:
                print(
                    "!!! ATENÇÃO: DEFAULT após RESET "
                    "não corresponde ao original !!!"
                )

            results[-1]["reset_current_ok"] = reset_current_ok
            results[-1]["reset_default_ok"] = reset_default_ok
            results[-1]["current_after_reset"] = (
                current_after_reset
            )
            results[-1]["default_after_reset"] = (
                default_after_reset
            )

        except Exception as exc:
            print()
            print(f"✗ ERRO durante RESET: {exc}")

    return results


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 SET / RESET MATRIX PROBE")
    print("=" * 72)

    print()
    print(f"Impressora: {HOST}")
    print(f"RAW:        {PORT}")

    print()
    print("Este teste:")
    print()
    print("- NAO executa DEFAULT.")
    print("- NAO altera DEFAULT.")
    print("- NAO envia jobs.")
    print("- NAO imprime paginas.")
    print("- executa SET somente no ambiente corrente.")
    print("- executa RESET após cada valor.")
    print("- verifica INQUIRE.")
    print("- verifica DINQUIRE.")
    print()

    print("Variáveis testadas:")
    print()

    for test in TESTS:
        print(
            f"- {test['name']}: "
            + ", ".join(test["values"])
        )

    print()

    answer = input("Continuar? [S/N]: ").strip().upper()

    if answer != "S":
        print()
        print("Teste cancelado.")
        return

    all_results = []

    for test in TESTS:
        result = test_variable(
            test["name"],
            test["values"],
        )

        if result:
            all_results.append(
                {
                    "variable": test["name"],
                    "results": result,
                }
            )

    print()
    print()
    print("=" * 72)
    print("RESUMO DA DESCOBERTA")
    print("=" * 72)

    print()

    for item in all_results:
        variable = item["variable"]

        print()
        print(f"[{variable}]")

        for result in item["results"]:
            value = result["value"]

            if result.get("error"):
                print(
                    f"  {value}: ERRO "
                    f"{result['error']}"
                )
                continue

            set_ok = result.get(
                "set_ok",
                False,
            )

            default_ok = result.get(
                "default_ok",
                False,
            )

            reset_current_ok = result.get(
                "reset_current_ok",
                False,
            )

            reset_default_ok = result.get(
                "reset_default_ok",
                False,
            )

            if (
                set_ok
                and default_ok
                and reset_current_ok
                and reset_default_ok
            ):
                status = "✓ SUPORTADA"
            elif set_ok:
                status = "⚠ SET PARCIAL"
            else:
                status = "✗ NAO CONFIRMADA"

            print(
                f"  {value:12} -> {status}"
            )

    print()
    print("=" * 72)
    print("FIM")
    print("=" * 72)

    print()
    print("Nenhum DEFAULT foi executado.")
    print("Nenhum job foi enviado.")
    print("Nenhuma pagina foi impressa.")
    print()
    print("Se todos os testes terminarem com RESET OK,")
    print("teremos uma matriz real de configuracao da MX611.")


if __name__ == "__main__":
    main()