"""
Printer Assistant - PJL Media SET / RESET Probe

Testa variáveis de mídia no ambiente corrente da impressora.

Este teste:
- não altera DEFAULT;
- não envia job;
- testa SET;
- verifica INQUIRE;
- verifica DINQUIRE;
- executa RESET;
- confirma a restauração.

A variável MEDIATYPE é testada apenas se a impressora
responder ao INQUIRE.
"""

import socket
import time


class PJLConnection:
    def __init__(self, ip, port=9100, timeout=3, retries=3):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.retries = retries

    def send(self, command, wait=0.20):
        last_error = None

        for attempt in range(1, self.retries + 1):
            sock = None

            try:
                print(
                    f"Conectando em {self.ip}:{self.port} "
                    f"(tentativa {attempt}/{self.retries})..."
                )

                sock = socket.create_connection(
                    (self.ip, self.port),
                    timeout=self.timeout,
                )

                sock.settimeout(self.timeout)

                if not command.endswith("\r\n"):
                    command += "\r\n"

                sock.sendall(
                    command.encode(
                        "ascii",
                        errors="replace",
                    )
                )

                if wait:
                    time.sleep(wait)

                response = bytearray()

                while True:
                    try:
                        block = sock.recv(4096)

                        if not block:
                            break

                        response.extend(block)

                        if len(block) < 4096:
                            break

                    except socket.timeout:
                        break

                return response.decode(
                    "latin-1",
                    errors="replace",
                )

            except Exception as exc:
                last_error = exc

                if attempt < self.retries:
                    time.sleep(0.5)

            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

        raise last_error


def clean_response(text):
    text = text.replace("\x0c", "")
    text = text.replace("\x00", "")
    return text.strip()


def inquire(connection, variable):
    try:
        response = connection.send(
            f"@PJL INQUIRE {variable}"
        )

        response = clean_response(response)

        if not response:
            return None

        lines = response.splitlines()

        for line in reversed(lines):
            line = line.strip()

            if not line:
                continue

            if line.upper().startswith("@PJL"):
                continue

            return line

        return None

    except Exception as exc:
        print(f"Erro em INQUIRE {variable}: {exc}")
        return None


def dinquire(connection, variable):
    try:
        response = connection.send(
            f"@PJL DINQUIRE {variable}"
        )

        response = clean_response(response)

        if not response:
            return None

        lines = response.splitlines()

        for line in reversed(lines):
            line = line.strip()

            if not line:
                continue

            if line.upper().startswith("@PJL"):
                continue

            return line

        return None

    except Exception as exc:
        print(f"Erro em DINQUIRE {variable}: {exc}")
        return None


def show_state(connection, variable):
    current = inquire(connection, variable)
    default = dinquire(connection, variable)

    print()
    print(variable)
    print(f"INQUIRE  : {current}")
    print(f"DINQUIRE : {default}")

    return current, default


def test_set_reset(
    connection,
    variable,
    test_value,
):
    print()
    print("=" * 72)
    print(f"TESTANDO {variable}")
    print("=" * 72)

    print()
    print("1. ESTADO ORIGINAL")
    print("-" * 72)

    original_current, original_default = show_state(
        connection,
        variable,
    )

    if original_current is None:
        print()
        print(
            f"⚠ A impressora não respondeu ao "
            f"INQUIRE {variable}."
        )
        print(
            "Variável não será alterada."
        )
        return

    if original_default is None:
        print()
        print(
            f"⚠ A impressora não respondeu ao "
            f"DINQUIRE {variable}."
        )
        print(
            "Variável não será alterada."
        )
        return

    print()
    print(f"Valor de teste: {test_value}")

    print()
    print(f"2. SET {variable}={test_value}")
    print("-" * 72)

    try:
        connection.send(
            f"@PJL SET {variable}={test_value}"
        )
    except Exception as exc:
        print(f"Erro ao enviar SET: {exc}")
        return

    current_after_set = inquire(
        connection,
        variable,
    )

    default_after_set = dinquire(
        connection,
        variable,
    )

    print()
    print("Estado após SET:")
    print(f"INQUIRE  : {current_after_set}")
    print(f"DINQUIRE : {default_after_set}")

    if current_after_set == test_value:
        print(
            f"✓ SET {variable}={test_value} "
            "alterou o ambiente corrente."
        )
    else:
        print(
            f"✗ SET {variable} não produziu "
            "o valor esperado."
        )

    if default_after_set == original_default:
        print(
            "✓ DEFAULT permaneceu inalterado."
        )
    else:
        print(
            "⚠ DEFAULT também foi alterado."
        )

    print()
    print("3. RESET")
    print("-" * 72)

    try:
        connection.send(
            "@PJL RESET"
        )
    except Exception as exc:
        print(f"Erro ao enviar RESET: {exc}")
        return

    current_after_reset = inquire(
        connection,
        variable,
    )

    default_after_reset = dinquire(
        connection,
        variable,
    )

    print()
    print("Estado após RESET:")
    print(f"INQUIRE  : {current_after_reset}")
    print(f"DINQUIRE : {default_after_reset}")

    print()
    print("4. RESULTADO")
    print("-" * 72)

    print(
        f"Original corrente   : {original_current}"
    )
    print(
        f"Original default    : {original_default}"
    )
    print(
        f"Após SET corrente   : {current_after_set}"
    )
    print(
        f"Após SET default    : {default_after_set}"
    )
    print(
        f"Após RESET corrente : {current_after_reset}"
    )
    print(
        f"Após RESET default  : {default_after_reset}"
    )

    if (
        current_after_set == test_value
        and default_after_set == original_default
    ):
        print()
        print(
            f"✓ {variable}: SET CONFIRMADO."
        )
    else:
        print()
        print(
            f"✗ {variable}: comportamento "
            "de SET não confirmado."
        )

    if (
        current_after_reset == original_current
        and default_after_reset == original_default
    ):
        print(
            f"✓ {variable}: RESET CONFIRMADO."
        )
    else:
        print(
            f"✗ {variable}: restauração "
            "diferente do original."
        )


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL MEDIA SET / RESET PROBE")
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(f"Impressora: {ip}")
    print("RAW:        9100")
    print()
    print("Este teste:")
    print()
    print("- NÃO altera DEFAULT.")
    print("- NÃO envia nenhum job.")
    print("- testa PAPER=A5.")
    print("- tenta descobrir MEDIATYPE.")
    print("- testa SET.")
    print("- executa RESET.")
    print("- verifica INQUIRE/DINQUIRE.")
    print()
    print(
        "IMPORTANTE: nenhuma alteração permanente "
        "será feita."
    )
    print()

    confirmation = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmation != "S":
        print("Teste cancelado.")
        return

    connection = PJLConnection(
        ip=ip,
        port=9100,
        timeout=3,
        retries=3,
    )

    print()
    print("=" * 72)
    print("1. TESTE PAPER")
    print("=" * 72)

    test_set_reset(
        connection,
        "PAPER",
        "A5",
    )

    print()
    print("=" * 72)
    print("2. DESCOBERTA MEDIATYPE")
    print("=" * 72)

    media_current = inquire(
        connection,
        "MEDIATYPE",
    )

    media_default = dinquire(
        connection,
        "MEDIATYPE",
    )

    print()
    print("MEDIATYPE")
    print(f"INQUIRE  : {media_current}")
    print(f"DINQUIRE : {media_default}")

    if media_current is None:
        print()
        print(
            "⚠ MEDIATYPE não respondeu ao INQUIRE."
        )
        print(
            "Nenhum SET MEDIATYPE será executado."
        )
    else:
        test_set_reset(
            connection,
            "MEDIATYPE",
            "PLAIN",
        )

    print()
    print("=" * 72)
    print("FINAL")
    print("=" * 72)
    print()
    print(
        "Nenhum DEFAULT foi alterado."
    )
    print(
        "Nenhum job foi enviado."
    )
    print(
        "Se MEDIATYPE não responder, "
        "não significa que a impressora não possui "
        "configuração de tipo de papel."
    )
    print(
        "Nesse caso vamos descobrir o nome exato "
        "da variável em uma bateria separada."
    )
    print()


if __name__ == "__main__":
    main()