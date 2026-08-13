"""
Printer Assistant - PJL Job Orientation Probe

Testa a influência da orientação definida explicitamente
dentro do próprio job PJL/PCL.

Este teste não altera DEFAULT.

Sequência:

1. Ler estado original.
2. Enviar job PCL sem ORIENTATION.
3. Enviar job PCL com @PJL SET ORIENTATION=LANDSCAPE.
4. Comparar o comportamento físico das páginas.
"""

import socket
import time


class PJLJobOrientationProbe:
    def __init__(self, ip, port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def ler(self, comando, espera=0.15):
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
        resposta = self.ler(
            f"@PJL INQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def dinquire(self, variavel):
        resposta = self.ler(
            f"@PJL DINQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def enviar_job(self, orientacao=None):
        partes = [
            b"\x1b%-12345X",
            b"@PJL JOB NAME=\"ORIENTATION_PROBE\"\r\n",
        ]

        if orientacao is not None:
            comando = (
                f"@PJL SET ORIENTATION={orientacao}\r\n"
            )

            partes.append(
                comando.encode("ascii")
            )

        partes.extend(
            [
                b"@PJL ENTER LANGUAGE=PCL\r\n",
                b"\x1b&l1O",
                b"\x1b&l0E",
                b"\x1b&l6D",
            ]
        )

        texto = (
            "\r\n"
            "PRINTER ASSISTANT\r\n"
            "\r\n"
            "PJL ORIENTATION PROBE\r\n"
            "\r\n"
            "TESTE DE ORIENTACAO\r\n"
            "\r\n"
        )

        partes.append(
            texto.encode(
                "cp850",
                errors="replace",
            )
        )

        partes.extend(
            [
                b"\x0c",
                b"\x1b%-12345X",
            ]
        )

        job = b"".join(partes)

        sock = None

        try:
            inicio = time.monotonic()

            sock = socket.create_connection(
                (self.ip, self.port),
                timeout=self.timeout,
            )

            sock.sendall(job)

            tempo = time.monotonic() - inicio

            return len(job), tempo

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def mostrar_estado(probe):
    corrente = probe.inquire("ORIENTATION")
    padrao = probe.dinquire("ORIENTATION")

    print(f"INQUIRE  : {corrente}")
    print(f"DINQUIRE : {padrao}")

    return corrente, padrao


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL JOB ORIENTATION PROBE")
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
    print("Serão enviadas duas páginas:")
    print()
    print("Página 1:")
    print("  Job PCL sem ORIENTATION explícito.")
    print()
    print("Página 2:")
    print("  Job com @PJL SET ORIENTATION=LANDSCAPE")
    print("  antes de entrar em PCL.")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    probe = PJLJobOrientationProbe(ip)

    print()
    print("=" * 72)
    print("ESTADO INICIAL")
    print("=" * 72)

    original_corrente, original_default = mostrar_estado(
        probe
    )

    print()
    print("=" * 72)
    print("PÁGINA 1 - SEM ORIENTATION PJL")
    print("=" * 72)

    print()
    print("A primeira página NÃO terá")
    print("@PJL SET ORIENTATION.")
    print()
    print("Observe fisicamente a orientação.")
    print()

    input(
        "Pressione ENTER para enviar a primeira página..."
    )

    bytes_1, tempo_1 = probe.enviar_job()

    print()
    print("Primeiro job enviado.")
    print(f"Bytes enviados: {bytes_1}")
    print(f"Tempo:          {tempo_1:.3f}s")

    print()
    print("=" * 72)
    print("PÁGINA 2 - ORIENTATION DENTRO DO JOB")
    print("=" * 72)

    print()
    print("A segunda página terá:")
    print()
    print("@PJL SET ORIENTATION=LANDSCAPE")
    print()
    print("antes de:")
    print()
    print("@PJL ENTER LANGUAGE=PCL")
    print()
    print("Observe fisicamente a orientação.")
    print()

    input(
        "Pressione ENTER para enviar a segunda página..."
    )

    bytes_2, tempo_2 = probe.enviar_job(
        orientacao="LANDSCAPE"
    )

    print()
    print("Segundo job enviado.")
    print(f"Bytes enviados: {bytes_2}")
    print(f"Tempo:          {tempo_2:.3f}s")

    print()
    print("=" * 72)
    print("RESTAURAÇÃO")
    print("=" * 72)

    probe.ler("@PJL RESET")

    corrente_final, default_final = mostrar_estado(
        probe
    )

    print()
    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    print()
    print(f"Original corrente : {original_corrente}")
    print(f"Original default  : {original_default}")
    print()
    print(f"Final corrente    : {corrente_final}")
    print(f"Final default     : {default_final}")

    print()

    if (
        str(corrente_final).upper()
        == str(original_corrente).upper()
        and
        str(default_final).upper()
        == str(original_default).upper()
    ):
        print("✓ ESTADO PJL RESTAURADO.")
    else:
        print("⚠ ESTADO FINAL DIFERENTE DO ORIGINAL.")

    print()
    print("Nenhum DEFAULT foi alterado.")
    print()
    print("Analise fisicamente as duas páginas:")
    print()
    print("Página 1 = sem ORIENTATION explícito")
    print("Página 2 = ORIENTATION=LANDSCAPE no job")
    print()


if __name__ == "__main__":
    main()