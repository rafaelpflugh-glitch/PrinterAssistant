
"""
Printer Assistant - PJL Command Probe

Descobre quais comandos PJL de consulta a impressora respondem.
Este módulo NÃO altera configurações da impressora.
"""

import socket
import time


class PJLCommandProbe:
    def __init__(self, ip, port=9100, timeout=3):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def enviar(self, comando, espera=0.20):
        sock = None

        try:
            sock = socket.create_connection(
                (self.ip, self.port),
                timeout=self.timeout,
            )

            sock.settimeout(self.timeout)

            if not comando.endswith("\r\n"):
                comando += "\r\n"

            inicio = time.monotonic()

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

            tempo = time.monotonic() - inicio

            return {
                "comando": comando.rstrip("\r\n"),
                "resposta": resposta.decode(
                    "latin-1",
                    errors="replace",
                ),
                "bytes": len(resposta),
                "tempo": tempo,
                "erro": None,
            }

        except Exception as exc:
            return {
                "comando": comando.rstrip("\r\n"),
                "resposta": "",
                "bytes": 0,
                "tempo": 0,
                "erro": str(exc),
            }

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    def testar(self, comandos):
        resultados = []

        for comando in comandos:
            resultados.append(
                self.enviar(comando)
            )

        return resultados


def imprimir_resultado(resultado):
    print()
    print("=" * 72)
    print(f"COMANDO: {resultado['comando']}")
    print("=" * 72)

    if resultado["erro"]:
        print(f"ERRO: {resultado['erro']}")
        return

    print(f"Bytes recebidos: {resultado['bytes']}")
    print(f"Tempo:           {resultado['tempo']:.3f}s")

    if resultado["resposta"]:
        print("RESPOSTA:")
        print(resultado["resposta"])
    else:
        print("RESPOSTA:")
        print("(sem resposta)")


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL COMMAND PROBE")
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
    print("Este teste NÃO altera configurações.")
    print("Serão testados somente comandos PJL de consulta.")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    comandos = [
        "@PJL INFO ID",
        "@PJL INFO VARIABLES",
        "@PJL INFO CONFIG",
        "@PJL INFO STATUS",
        "@PJL INFO PRODINFO",
        "@PJL INQUIRE LANG",
        "@PJL DINQUIRE LANG",
    ]

    probe = PJLCommandProbe(
        ip=ip,
        port=9100,
        timeout=3,
    )

    print()
    print("=" * 72)
    print("EXECUTANDO COMANDOS")
    print("=" * 72)

    resultados = probe.testar(comandos)

    for resultado in resultados:
        imprimir_resultado(resultado)

    print()
    print("=" * 72)
    print("RESUMO")
    print("=" * 72)

    for resultado in resultados:
        if resultado["erro"]:
            status = "ERRO"
        elif resultado["resposta"]:
            status = "RESPONDEU"
        else:
            status = "SEM RESPOSTA"

        print(
            f"{status:15} "
            f"{resultado['comando']}"
        )

    print()
    print("Nenhuma configuração foi alterada.")
    print()


if __name__ == "__main__":
    main()
