"""
Printer Assistant - PJL Duplex Job Probe

Investiga o comportamento do DUPLEX no contexto de um job PCL.

O teste não altera DEFAULT.

Sequência:

1. Ler estado original.
2. SET DUPLEX=ON.
3. Confirmar INQUIRE/DINQUIRE.
4. Enviar job PCL sem comando de duplex.
5. RESET.
6. Confirmar restauração.
7. Enviar segundo job PCL sem comando de duplex.

Objetivo:

Descobrir se o estado corrente definido por SET DUPLEX
é utilizado pelo processamento do job PCL.
"""

import socket
import time


class PJLDuplexJobProbe:
    def __init__(self, ip, port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def enviar_pjl(self, comando, espera=0.15):
        sock = None

        try:
            sock = socket.create_connection(
                (self.ip, self.port),
                timeout=self.timeout,
            )

            sock.settimeout(self.timeout)

            if not comando.endswith("\r\n"):
                comando += "\r\n"

            sock.sendall(
                comando.encode(
                    "ascii",
                    errors="replace",
                )
            )

            if espera:
                time.sleep(espera)

            resposta = bytearray()

            while True:
                try:
                    bloco = sock.recv(4096)

                    if not bloco:
                        break

                    resposta.extend(bloco)

                    if len(bloco) < 4096:
                        break

                except socket.timeout:
                    break

            return resposta.decode(
                "latin-1",
                errors="replace",
            )

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    @staticmethod
    def extrair_valor(resposta):
        if not resposta:
            return None

        for linha in resposta.splitlines():
            linha = linha.strip()

            if not linha:
                continue

            if linha.upper().startswith("@PJL"):
                continue

            return linha.strip('"')

        return None

    def inquire(self, variavel):
        resposta = self.enviar_pjl(
            f"@PJL INQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def dinquire(self, variavel):
        resposta = self.enviar_pjl(
            f"@PJL DINQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def set_variavel(self, variavel, valor):
        self.enviar_pjl(
            f"@PJL SET {variavel}={valor}"
        )

    def reset(self):
        self.enviar_pjl("@PJL RESET")

    def enviar_job(self, numero):
        linhas = [
            "\r\n",
            "PRINTER ASSISTANT\r\n",
            "\r\n",
            f"DUPLEX JOB TEST {numero}\r\n",
            "\r\n",
            "PAGINA 1\r\n",
            "\r\n",
            "DUPLEX PROBE\r\n",
            "\r\n",
        ]

        texto = "".join(linhas)

        job = bytearray()

        job.extend(b"\x1b%-12345X")

        job.extend(
            b'@PJL JOB NAME="DUPLEX_PROBE"\r\n'
        )

        job.extend(
            b"@PJL ENTER LANGUAGE=PCL\r\n"
        )

        job.extend(
            b"\x1b&l0O"
        )

        job.extend(
            texto.encode(
                "cp850",
                errors="replace",
            )
        )

        job.extend(
            b"\x0c"
        )

        job.extend(
            b"\x1b%-12345X"
        )

        sock = None

        try:
            inicio = time.monotonic()

            sock = socket.create_connection(
                (self.ip, self.port),
                timeout=self.timeout,
            )

            sock.sendall(bytes(job))

            tempo = time.monotonic() - inicio

            return len(job), tempo

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def mostrar_estado(probe):
    corrente = probe.inquire("DUPLEX")
    padrao = probe.dinquire("DUPLEX")

    print(f"INQUIRE  : {corrente}")
    print(f"DINQUIRE : {padrao}")

    return corrente, padrao


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL DUPLEX JOB PROBE")
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

    print("Este teste NÃO altera DEFAULT.")
    print()
    print("Serão enviados dois jobs.")
    print()
    print("JOB 1:")
    print("  SET DUPLEX=ON")
    print("  PCL sem comando explícito de duplex")
    print()
    print("JOB 2:")
    print("  após RESET")
    print("  PCL sem comando explícito de duplex")
    print()

    print("ATENÇÃO:")
    print("A impressora poderá imprimir frente e verso.")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    probe = PJLDuplexJobProbe(ip)

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    original_corrente, original_default = mostrar_estado(
        probe
    )

    print()
    print("=" * 72)
    print("2. SET DUPLEX=ON")
    print("=" * 72)

    print()
    print("Enviando:")
    print("@PJL SET DUPLEX=ON")

    probe.set_variavel(
        "DUPLEX",
        "ON",
    )

    corrente_set, default_set = mostrar_estado(
        probe
    )

    print()

    if str(corrente_set).upper() == "ON":
        print("✓ SET ALTEROU O AMBIENTE CORRENTE.")
    else:
        print("✗ SET NÃO ALTEROU O AMBIENTE CORRENTE.")

    if str(default_set).upper() == str(
        original_default
    ).upper():
        print("✓ DEFAULT PERMANECEU INALTERADO.")
    else:
        print("✗ DEFAULT FOI ALTERADO.")

    print()
    print("=" * 72)
    print("3. JOB 1")
    print("=" * 72)

    print()
    print("O job NÃO contém:")
    print()
    print("@PJL SET DUPLEX=...")
    print()
    print("Portanto ele deverá utilizar o ambiente corrente.")
    print()

    input(
        "Pressione ENTER para enviar o primeiro job..."
    )

    bytes_1, tempo_1 = probe.enviar_job(1)

    print()
    print("Primeiro job enviado.")
    print(f"Bytes enviados: {bytes_1}")
    print(f"Tempo:          {tempo_1:.3f}s")

    print()
    print("Observe fisicamente:")
    print()
    print("- se houve impressão frente e verso;"
    )
    print("- se houve apenas uma face;"
    )
    print("- comportamento geral do job.")
    print()

    input(
        "Pressione ENTER depois de analisar a página..."
    )

    print()
    print("=" * 72)
    print("4. RESET")
    print("=" * 72)

    print()
    print("Enviando:")
    print("@PJL RESET")

    probe.reset()

    corrente_reset, default_reset = mostrar_estado(
        probe
    )

    print()

    if str(corrente_reset).upper() == str(
        original_default
    ).upper():
        print(
            "✓ RESET RESTAUROU O AMBIENTE CORRENTE."
        )
    else:
        print(
            "✗ RESET NÃO RESTAUROU O AMBIENTE CORRENTE."
        )

    if str(default_reset).upper() == str(
        original_default
    ).upper():
        print(
            "✓ DEFAULT PERMANECEU NO VALOR ORIGINAL."
        )
    else:
        print(
            "✗ DEFAULT FOI ALTERADO."
        )

    print()
    print("=" * 72)
    print("5. JOB 2")
    print("=" * 72)

    print()
    print("Agora o ambiente corrente foi restaurado.")
    print()
    print("O segundo job também NÃO contém")
    print("nenhum comando explícito de duplex.")
    print()

    input(
        "Pressione ENTER para enviar o segundo job..."
    )

    bytes_2, tempo_2 = probe.enviar_job(2)

    print()
    print("Segundo job enviado.")
    print(f"Bytes enviados: {bytes_2}")
    print(f"Tempo:          {tempo_2:.3f}s")

    print()
    print("Observe fisicamente a segunda impressão.")
    print()

    input(
        "Pressione ENTER depois de analisar a página..."
    )

    print()
    print("=" * 72)
    print("6. ESTADO FINAL")
    print("=" * 72)

    corrente_final, default_final = mostrar_estado(
        probe
    )

    print()
    print(f"Original corrente : {original_corrente}")
    print(f"Original default  : {original_default}")
    print()
    print(f"Final corrente    : {corrente_final}")
    print(f"Final default     : {default_final}")

    print()

    corrente_ok = (
        str(corrente_final).upper()
        == str(original_corrente).upper()
    )

    default_ok = (
        str(default_final).upper()
        == str(original_default).upper()
    )

    if corrente_ok:
        print("✓ CORRENTE RESTAURADO.")
    else:
        print("✗ CORRENTE DIFERENTE DO ORIGINAL.")

    if default_ok:
        print("✓ DEFAULT RESTAURADO.")
    else:
        print("✗ DEFAULT DIFERENTE DO ORIGINAL.")

    print()
    print("=" * 72)
    print("FIM DO TESTE")
    print("=" * 72)
    print()
    print("Nenhum DEFAULT foi alterado.")
    print()
    print("Compare fisicamente:")
    print()
    print("JOB 1 = SET DUPLEX=ON")
    print("JOB 2 = após RESET")
    print()


if __name__ == "__main__":
    main()