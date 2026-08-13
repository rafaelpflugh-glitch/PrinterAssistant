import socket
import time
from dataclasses import dataclass


RAW_PORT = 9100
CONNECT_TIMEOUT = 5.0
RETRIES = 3
RETRY_DELAY = 0.25


@dataclass
class ProbeResult:
    variable: str
    expected: str
    original_current: str | None
    original_default: str | None
    after_set_current: str | None
    after_set_default: str | None
    after_reset_current: str | None
    after_reset_default: str | None
    set_ok: bool
    reset_ok: bool
    default_preserved: bool


class PJLProbe:
    def __init__(self, ip: str):
        self.ip = ip
        self.port = RAW_PORT

    def _connect(self):
        last_error = None

        for attempt in range(1, RETRIES + 1):
            print(
                f"Conectando em {self.ip}:{self.port} "
                f"(tentativa {attempt}/{RETRIES})..."
            )

            try:
                sock = socket.create_connection(
                    (self.ip, self.port),
                    timeout=CONNECT_TIMEOUT,
                )
                sock.settimeout(2.0)
                return sock

            except OSError as exc:
                last_error = exc

                if attempt < RETRIES:
                    time.sleep(RETRY_DELAY)

        raise last_error

    def _send(self, command: str, read_response: bool = True):
        payload = (
            "\x1b%-12345X"
            + command
            + "\r\n"
        ).encode("ascii", errors="replace")

        with self._connect() as sock:
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

                    if len(data) < 4096:
                        break

                except socket.timeout:
                    break

        return b"".join(chunks).decode(
            "latin-1",
            errors="replace",
        )

    @staticmethod
    def _clean_response(response: str):
        text = response.replace("\x1b", "")
        lines = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            if line.startswith("%-12345X"):
                line = line[len("%-12345X"):].strip()

            lines.append(line)

        if not lines:
            return None

        return lines[-1]

    def inquire(self, variable: str):
        response = self._send(
            f"@PJL INQUIRE {variable}",
            read_response=True,
        )

        return self._clean_response(response)

    def dinquire(self, variable: str):
        response = self._send(
            f"@PJL DINQUIRE {variable}",
            read_response=True,
        )

        return self._clean_response(response)

    def set_variable(self, variable: str, value: str):
        self._send(
            f"@PJL SET {variable}={value}",
            read_response=False,
        )

    def reset(self):
        self._send(
            "@PJL RESET",
            read_response=False,
        )

    def probe_variable(self, variable: str, value: str):
        print()
        print("=" * 72)
        print(f"VARIÁVEL: {variable}")
        print("=" * 72)

        print()
        print("1. ESTADO ORIGINAL")
        print()

        original_current = self.inquire(variable)
        original_default = self.dinquire(variable)

        print(f"INQUIRE  : {original_current}")
        print(f"DINQUIRE : {original_default}")

        print()
        print(f"2. SET {variable}={value}")
        print()

        started = time.perf_counter()

        try:
            self.set_variable(variable, value)
        except OSError as exc:
            print(f"ERRO NO SET: {exc}")
            return ProbeResult(
                variable=variable,
                expected=value,
                original_current=original_current,
                original_default=original_default,
                after_set_current=None,
                after_set_default=None,
                after_reset_current=None,
                after_reset_default=None,
                set_ok=False,
                reset_ok=False,
                default_preserved=False,
            )

        elapsed = time.perf_counter() - started
        print(f"SET enviado em {elapsed:.3f}s")

        after_set_current = self.inquire(variable)
        after_set_default = self.dinquire(variable)

        print()
        print("Estado após SET:")
        print(f"INQUIRE  : {after_set_current}")
        print(f"DINQUIRE : {after_set_default}")

        set_ok = after_set_current == value
        default_preserved = after_set_default == original_default

        if set_ok:
            print(f"✓ SET {variable}={value} foi aceito.")
        else:
            print(
                f"✗ SET {variable}={value} "
                f"não produziu o valor esperado."
            )

        if default_preserved:
            print("✓ DEFAULT permaneceu inalterado.")
        else:
            print("✗ DEFAULT foi alterado.")

        print()
        print("3. RESET")
        print()

        started = time.perf_counter()
        self.reset()
        elapsed = time.perf_counter() - started

        print(f"RESET enviado em {elapsed:.3f}s")

        after_reset_current = self.inquire(variable)
        after_reset_default = self.dinquire(variable)

        print()
        print("Estado após RESET:")
        print(f"INQUIRE  : {after_reset_current}")
        print(f"DINQUIRE : {after_reset_default}")

        reset_ok = (
            after_reset_current == original_current
            and after_reset_default == original_default
        )

        if reset_ok:
            print("✓ RESET restaurou o estado original.")
        else:
            print("✗ RESET não restaurou exatamente o estado original.")

        return ProbeResult(
            variable=variable,
            expected=value,
            original_current=original_current,
            original_default=original_default,
            after_set_current=after_set_current,
            after_set_default=after_set_default,
            after_reset_current=after_reset_current,
            after_reset_default=after_reset_default,
            set_ok=set_ok,
            reset_ok=reset_ok,
            default_preserved=default_preserved,
        )


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 PRINT CONTROL CAPABILITY PROBE")
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
    print("- NÃO altera DEFAULT.")
    print("- NÃO envia nenhum job.")
    print("- NÃO imprime nenhuma página.")
    print("- testa apenas SET temporário.")
    print("- verifica INQUIRE.")
    print("- verifica DINQUIRE.")
    print("- executa RESET após cada variável.")
    print("- confirma restauração.")
    print()

    tests = [
        ("RESOLUTION", "1200"),
        ("RESOLUTION", "300"),
        ("DENSITY", "1"),
        ("DENSITY", "2"),
        ("DENSITY", "4"),
        ("ORIENTATION", "LANDSCAPE"),
        ("ORIENTATION", "PORTRAIT"),
        ("COPIES", "2"),
        ("COPIES", "3"),
        ("DUPLEX", "ON"),
        ("DUPLEX", "OFF"),
    ]

    print("Variáveis/valores que serão testados:")
    print()

    for variable, value in tests:
        print(f"- {variable}={value}")

    print()
    answer = input("Continuar? [S/N]: ").strip().upper()

    if answer != "S":
        print("Teste cancelado.")
        return

    probe = PJLProbe(ip)
    results = []

    for variable, value in tests:
        result = probe.probe_variable(variable, value)
        results.append(result)

    print()
    print("=" * 72)
    print("RESUMO")
    print("=" * 72)
    print()
    print(
        f"{'VARIÁVEL':<15}"
        f"{'VALOR':<10}"
        f"{'SET':<8}"
        f"{'RESET':<9}"
        f"{'DEFAULT':<10}"
    )

    for result in results:
        set_status = "✓" if result.set_ok else "✗"
        reset_status = "✓" if result.reset_ok else "✗"
        default_status = "✓" if result.default_preserved else "✗"

        print(
            f"{result.variable:<15}"
            f"{result.expected:<10}"
            f"{set_status:<8}"
            f"{reset_status:<9}"
            f"{default_status:<10}"
        )

    print()
    print("Interpretação:")
    print()
    print("- SET ✓ = a variável aceitou o valor no ambiente corrente.")
    print("- RESET ✓ = RESET devolveu o valor original.")
    print("- DEFAULT ✓ = DINQUIRE permaneceu inalterado.")
    print()
    print("Nenhum job foi enviado.")
    print("Nenhuma página foi impressa.")


if __name__ == "__main__":
    main()