"""
Printer Assistant - PJL COPIES Job Probe

Testa o comportamento de PJL SET COPIES dentro de um job.

Este teste:
- não altera DEFAULT;
- não altera configurações persistentes;
- testa COPIES=1;
- testa COPIES=2;
- envia uma única página PCL em cada job;
- restaura o ambiente com PJL RESET.
"""

import socket
import time


class CopiesJobProbe:
    def __init__(self, ip, port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def conectar(self):
        sock = socket.create_connection(
            (self.ip, self.port),
            timeout=self.timeout,
        )

        sock.settimeout(self.timeout)

        return sock

    def consultar(self, variavel):
        respostas = {
            "inquire": None,
            "dinquire": None,
        }

        comandos = [
            (
                "inquire",
                f"@PJL INQUIRE {variavel}\r\n",
            ),
            (
                "dinquire",
                f"@PJL DINQUIRE {variavel}\r\n",
            ),
        ]

        for nome, comando in comandos:
            sock = None

            try:
                sock = self.conectar()

                sock.sendall(
                    comando.encode("ascii")
                )

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

                texto = resposta.decode(
                    "latin-1",
                    errors="replace",
                )

                linhas = [
                    linha.strip()
                    for linha in texto.splitlines()
                    if linha.strip()
                ]

                if linhas:
                    respostas[nome] = linhas[-1]

            except Exception:
                respostas[nome] = None

            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

        return respostas

    def enviar_comando(self, comando):
        sock = None

        try:
            sock = self.conectar()

            if not comando.endswith("\r\n"):
                comando += "\r\n"

            sock.sendall(
                comando.encode("ascii")
            )

            time.sleep(0.20)

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    def reset(self):
        self.enviar_comando("@PJL RESET")

    def construir_job(self, copies):
        pjl = (
            "@PJL JOB NAME=\"COPIES_PROBE\"\r\n"
            f"@PJL SET COPIES={copies}\r\n"
            "@PJL ENTER LANGUAGE=PCL\r\n"
        )

        pcl = bytearray()

        pcl.extend(b"\x1bE")

        pcl.extend(b"\x1b&l0O")
        pcl.extend(b"\x1b&l6D")

        pcl.extend(b"\x1b&a0L")

        pcl.extend(b"\x1b(s0p16.67h8.5v0s0b0T")

        pcl.extend(
            b"\x1b*p100x100Y"
        )

        texto = (
            f"PRINTER ASSISTANT - COPIES={copies}"
        )

        pcl.extend(
            f"\x1b&a0H".encode("ascii")
        )

        pcl.extend(
            texto.encode("ascii")
        )

        pcl.extend(b"\x0c")

        pcl.extend(b"\x1bE")

        return (
            pjl.encode("ascii")
            + bytes(pcl)
        )

    def enviar_job(self, copies):
        dados = self.construir_job(copies)

        inicio = time.monotonic()

        sock = None

        try:
            sock = self.conectar()

            sock.sendall(dados)

            tempo = time.monotonic() - inicio

            return len(dados), tempo

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def esperar_enter(mensagem):
    input(mensagem)


def imprimir_estado(probe):
    estado = probe.consultar("COPIES")

    print(
        f"INQUIRE  : {estado['inquire']}"
    )

    print(
        f"DINQUIRE : {estado['dinquire']}"
    )

    return estado


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL COPIES JOB PROBE")
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

    print(
        "Este teste NÃO altera DEFAULT."
    )

    print()
    print("Serão enviados dois jobs:")
    print()
    print("JOB A")
    print("PJL SET COPIES=1")
    print("1 página PCL")
    print()
    print("JOB B")
    print("PJL SET COPIES=2")
    print("1 página PCL")
    print()
    print(
        "Se COPIES for obedecido, o JOB B deverá"
    )
    print(
        "produzir duas cópias da mesma página."
    )
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    probe = CopiesJobProbe(
        ip=ip,
        port=9100,
        timeout=5,
    )

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    original = imprimir_estado(probe)

    original_current = original["inquire"]
    original_default = original["dinquire"]

    print()
    print(
        f"Corrente original : {original_current}"
    )
    print(
        f"Default original  : {original_default}"
    )

    print()
    print("=" * 72)
    print("2. JOB A - COPIES=1")
    print("=" * 72)

    print()
    print("@PJL SET COPIES=1")
    print("@PJL ENTER LANGUAGE=PCL")
    print()
    print("Uma página será enviada.")

    esperar_enter(
        "Pressione ENTER para enviar o JOB A..."
    )

    try:
        bytes_a, tempo_a = probe.enviar_job(1)

        print()
        print("JOB A enviado.")
        print(
            f"Bytes enviados: {bytes_a}"
        )
        print(
            f"Tempo:          {tempo_a:.3f}s"
        )

    except Exception as exc:
        print()
        print(
            f"ERRO AO ENVIAR JOB A: {exc}"
        )
        return

    print()
    print(
        "Observe fisicamente:"
    )
    print(
        "- quantas folhas foram usadas;"
    )
    print(
        "- quantas páginas foram impressas."
    )

    esperar_enter(
        "Pressione ENTER para continuar..."
    )

    print()
    print("=" * 72)
    print("3. RESET APÓS JOB A")
    print("=" * 72)

    try:
        probe.reset()
        time.sleep(0.3)
    except Exception as exc:
        print(
            f"ERRO NO RESET: {exc}"
        )
        return

    print()
    imprimir_estado(probe)

    print()
    print("=" * 72)
    print("4. JOB B - COPIES=2")
    print("=" * 72)

    print()
    print("@PJL SET COPIES=2")
    print("@PJL ENTER LANGUAGE=PCL")
    print()
    print(
        "Uma única página PCL será enviada."
    )

    print(
        "O PJL solicitará duas cópias."
    )

    esperar_enter(
        "Pressione ENTER para enviar o JOB B..."
    )

    try:
        bytes_b, tempo_b = probe.enviar_job(2)

        print()
        print("JOB B enviado.")
        print(
            f"Bytes enviados: {bytes_b}"
        )
        print(
            f"Tempo:          {tempo_b:.3f}s"
        )

    except Exception as exc:
        print()
        print(
            f"ERRO AO ENVIAR JOB B: {exc}"
        )
        return

    print()
    print(
        "Observe fisicamente:"
    )
    print(
        "- quantas folhas foram usadas;"
    )
    print(
        "- quantas páginas foram impressas;"
    )
    print(
        "- se as duas cópias são idênticas."
    )

    esperar_enter(
        "Pressione ENTER para finalizar..."
    )

    print()
    print("=" * 72)
    print("5. RESET FINAL")
    print("=" * 72)

    try:
        probe.reset()
        time.sleep(0.3)
    except Exception as exc:
        print(
            f"ERRO NO RESET FINAL: {exc}"
        )

    print()
    print("=" * 72)
    print("6. ESTADO FINAL")
    print("=" * 72)

    final = imprimir_estado(probe)

    final_current = final["inquire"]
    final_default = final["dinquire"]

    print()
    print(
        f"Corrente original : {original_current}"
    )
    print(
        f"Default original  : {original_default}"
    )
    print(
        f"Corrente final    : {final_current}"
    )
    print(
        f"Default final     : {final_default}"
    )

    if (
        final_current == original_current
        and final_default == original_default
    ):
        print()
        print(
            "✓ ESTADO PJL RESTAURADO."
        )
    else:
        print()
        print(
            "⚠ ESTADO FINAL DIFERE DO ORIGINAL."
        )

    print()
    print("=" * 72)
    print("RESULTADO FÍSICO")
    print("=" * 72)

    print()
    print(
        "JOB A = COPIES=1 + 1 página PCL"
    )

    print(
        "JOB B = COPIES=2 + 1 página PCL"
    )

    print()
    print(
        "Anote quantas páginas foram realmente"
    )
    print(
        "produzidas em cada job."
    )

    print()
    print(
        "Nenhum DEFAULT foi alterado."
    )

    print()


if __name__ == "__main__":
    main()