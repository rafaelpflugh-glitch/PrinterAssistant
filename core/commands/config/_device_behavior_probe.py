import socket
import time


HOST = input("Digite o IP da impressora: ").strip()
PORT = 9100
TIMEOUT = 3.0


VARIABLES = [
    ("LANG", "ENGLISH"),
    ("LANGUAGE", "ENGLISH"),
    ("TIMEZONE", "UTC"),
    ("COUNTRY", "USA"),
    ("COUNTRYCODE", "US"),
    ("OUTPUTBIN", "UPPER"),
    ("MEDIASOURCE", "TRAY1"),
    ("TRAY", "TRAY1"),
    ("INPUTTRAY", "TRAY1"),
]


def connect():
    sock = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
    sock.settimeout(TIMEOUT)
    return sock


def send_raw(data):
    sock = connect()
    try:
        sock.sendall(data)
    finally:
        sock.close()


def inquire(variable, default=False):
    command = (
        f"@PJL DINQUIRE {variable}\r\n"
        if default
        else f"@PJL INQUIRE {variable}\r\n"
    )

    sock = connect()

    try:
        sock.sendall(command.encode("ascii"))

        data = b""

        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break

                data += chunk

                if b"\x0c" in data:
                    break

            except socket.timeout:
                break

        text = data.decode("latin-1", errors="replace").strip()

        return clean_response(text)

    finally:
        sock.close()


def clean_response(text):
    if not text:
        return None

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("@PJL INQUIRE"):
            continue

        if line.startswith("@PJL DINQUIRE"):
            continue

        lines.append(line)

    if not lines:
        return None

    return lines[-1]


def set_variable(variable, value):
    command = f"@PJL SET {variable}={value}\r\n"

    start = time.perf_counter()
    send_raw(command.encode("ascii"))
    elapsed = time.perf_counter() - start

    return elapsed


def reset():
    command = "@PJL RESET\r\n"

    start = time.perf_counter()
    send_raw(command.encode("ascii"))
    elapsed = time.perf_counter() - start

    return elapsed


def test_variable(variable, test_value):
    print()
    print("=" * 72)
    print(f"VARIAVEL: {variable}")
    print("=" * 72)

    print()
    print("1. ESTADO ORIGINAL")
    print("-" * 72)

    current_original = inquire(variable)
    default_original = inquire(variable, default=True)

    print(f"INQUIRE  : {current_original}")
    print(f"DINQUIRE : {default_original}")

    print()
    print(f"2. SET {variable}={test_value}")
    print("-" * 72)

    try:
        elapsed = set_variable(variable, test_value)
        print(f"SET enviado em {elapsed:.3f}s")
    except Exception as exc:
        print(f"ERRO AO ENVIAR SET: {exc}")
        return {
            "variable": variable,
            "original": current_original,
            "default": default_original,
            "after_set": None,
            "after_reset": None,
            "set_confirmed": False,
        }

    time.sleep(0.2)

    current_after_set = inquire(variable)
    default_after_set = inquire(variable, default=True)

    print()
    print("Estado após SET:")
    print(f"INQUIRE  : {current_after_set}")
    print(f"DINQUIRE : {default_after_set}")

    set_confirmed = current_after_set == test_value

    if set_confirmed:
        print(f"✓ SET {variable}={test_value} alterou o ambiente corrente.")
    else:
        print(f"✗ SET {variable}={test_value} não produziu o valor esperado.")

    if default_after_set == default_original:
        print("✓ DEFAULT permaneceu inalterado.")
    else:
        print("⚠ DEFAULT mudou!")

    print()
    print("3. RESET")
    print("-" * 72)

    try:
        elapsed = reset()
        print(f"RESET enviado em {elapsed:.3f}s")
    except Exception as exc:
        print(f"ERRO AO ENVIAR RESET: {exc}")

    time.sleep(0.2)

    current_after_reset = inquire(variable)
    default_after_reset = inquire(variable, default=True)

    print()
    print("Estado após RESET:")
    print(f"INQUIRE  : {current_after_reset}")
    print(f"DINQUIRE : {default_after_reset}")

    reset_confirmed = current_after_reset == current_original

    if reset_confirmed:
        print("✓ RESET devolveu o ambiente ao estado original.")
    else:
        print("✗ RESET não devolveu o ambiente ao estado original.")

    if default_after_reset == default_original:
        print("✓ DEFAULT continua preservado.")
    else:
        print("⚠ DEFAULT final diferente do original!")

    return {
        "variable": variable,
        "original": current_original,
        "default": default_original,
        "after_set": current_after_set,
        "after_reset": current_after_reset,
        "set_confirmed": set_confirmed,
        "reset_confirmed": reset_confirmed,
        "default_preserved": default_after_reset == default_original,
    }


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 DEVICE BEHAVIOR PROBE")
    print("=" * 72)

    print()
    print(f"Impressora: {HOST}")
    print(f"RAW:        {PORT}")

    print()
    print("Este teste:")
    print()
    print("- testa variaveis fora do bloco de papel;");
    print("- executa SET temporario;");
    print("- verifica INQUIRE;");
    print("- verifica DINQUIRE;");
    print("- executa RESET;");
    print("- confirma restauracao;");
    print("- NAO altera DEFAULT;");
    print("- NAO envia nenhum job;");
    print("- NAO imprime nenhuma pagina.")

    print()
    print("Variaveis que serao investigadas:")
    print()

    for variable, value in VARIABLES:
        print(f"- {variable}: {value}")

    print()
    answer = input("Continuar? [S/N]: ").strip().upper()

    if answer != "S":
        print("Teste cancelado.")
        return

    results = []

    for variable, value in VARIABLES:
        result = test_variable(variable, value)
        results.append(result)

    print()
    print("=" * 72)
    print("RESUMO FINAL")
    print("=" * 72)

    print()
    print(
        f"{'VARIAVEL':<16}"
        f"{'SET':<10}"
        f"{'RESET':<10}"
        f"{'DEFAULT':<12}"
    )

    print("-" * 48)

    for result in results:
        variable = result["variable"]

        set_status = "✓" if result.get("set_confirmed") else "✗"
        reset_status = "✓" if result.get("reset_confirmed") else "✗"
        default_status = "✓" if result.get("default_preserved") else "✗"

        print(
            f"{variable:<16}"
            f"{set_status:<10}"
            f"{reset_status:<10}"
            f"{default_status:<12}"
        )

    confirmed = sum(
        1 for result in results
        if result.get("set_confirmed")
    )

    reset_confirmed = sum(
        1 for result in results
        if result.get("reset_confirmed")
    )

    defaults_preserved = sum(
        1 for result in results
        if result.get("default_preserved")
    )

    print()
    print(f"Variaveis testadas      : {len(results)}")
    print(f"SET confirmados        : {confirmed}/{len(results)}")
    print(f"RESET confirmados      : {reset_confirmed}/{len(results)}")
    print(f"DEFAULT preservado     : {defaults_preserved}/{len(results)}")

    print()
    print("=" * 72)
    print("FIM DO TESTE")
    print("=" * 72)


if __name__ == "__main__":
    main()