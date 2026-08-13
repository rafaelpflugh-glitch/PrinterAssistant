"""
Printer Assistant - PJL PAPER SET / RESET Probe

Testa o comportamento da variável PJL PAPER.

Este teste:
- não altera o DEFAULT;
- altera temporariamente somente o ambiente corrente;
- verifica INQUIRE;
- verifica DINQUIRE;
- executa RESET;
- confirma a restauração.

Nenhum job de impressão é enviado.
"""

import socket
import time


class PJLConnection:
    def __init__(self, ip, port=9100, timeout=3, retries=3):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.retries = retries

    def executar(self, comando, espera=0.20):
        ultimo_erro = None

        for tentativa in range(1, self.retries + 1):
            sock = None

            try:
                print(
                    f"Conectando em {self.ip}:{self.port} "
                    f"(tentativa {tentativa}/{self.retries})..."
                )

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

                texto = resposta.decode(
                    "latin-1",
                    errors="replace",
                )

                return texto.strip()

            except Exception as exc:
                ultimo_erro = exc

                if tentativa < self.retries:
                    time.sleep(0.5)

            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

        raise ConnectionError(
            f"Não foi possível conectar em "
            f"{self.ip}:{self.port}: {ultimo_erro}"
        )


def limpar_resposta(texto):
    if texto is None:
        return None

    texto = texto.replace("\x0c", "")
    texto = texto.replace("\x00", "")
    texto = texto.strip()

    if not texto:
        return None

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    if not linhas:
        return None

    return linhas[-1]


def inquire(pjl, variavel):
    resposta = pjl.executar(
        f"@PJL INQUIRE {variavel}"
    )

    return limpar_resposta(resposta)


def dinquire(pjl, variavel):
    resposta = pjl.executar(
        f"@PJL DINQUIRE {variavel}"
    )

    return limpar_resposta(resposta)


def imprimir_estado(pjl, variavel, titulo):
    print()
    print(titulo)
    print("-" * 72)

    corrente = inquire(pjl, variavel)
    padrao = dinquire(pjl, variavel)

    print(f"INQUIRE  : {corrente}")
    print(f"DINQUIRE : {padrao}")

    return corrente, padrao


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL PAPER SET / RESET PROBE")
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
    print("Variável controlada:")
    print("PAPER")
    print()
    print("Valor de teste:")
    print("A5")
    print()
    print("Este teste:")
    print()
    print("- NÃO altera o DEFAULT.")
    print("- testa SET PAPER=A5.")
    print("- verifica INQUIRE.")
    print("- verifica DINQUIRE.")
    print("- executa RESET.")
    print("- confirma a restauração.")
    print()
    print("NENHUM JOB SERÁ IMPRESSO.")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    pjl = PJLConnection(ip)

    variavel = "PAPER"
    valor_teste = "A5"

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    corrente_original = inquire(pjl, variavel)
    default_original = dinquire(pjl, variavel)

    print(f"INQUIRE  : {corrente_original}")
    print(f"DINQUIRE : {default_original}")

    if corrente_original is None:
        print()
        print("Não foi possível obter o valor corrente.")
        print("Teste interrompido.")
        return

    if default_original is None:
        print()
        print("Não foi possível obter o DEFAULT.")
        print("Teste interrompido.")
        return

    print()
    print("=" * 72)
    print("2. SET PAPER=A5")
    print("=" * 72)

    print()
    print("@PJL SET PAPER=A5")

    pjl.executar(
        "@PJL SET PAPER=A5",
        espera=0.30,
    )

    corrente_apos_set = inquire(pjl, variavel)
    default_apos_set = dinquire(pjl, variavel)

    print()
    print("Após SET:")
    print(f"INQUIRE  : {corrente_apos_set}")
    print(f"DINQUIRE : {default_apos_set}")

    if corrente_apos_set == valor_teste:
        print()
        print("✓ SET PAPER=A5 alterou o ambiente corrente.")
    else:
        print()
        print("✗ SET PAPER=A5 NÃO produziu o valor esperado.")

    if default_apos_set == default_original:
        print("✓ DEFAULT permaneceu inalterado.")
    else:
        print("✗ DEFAULT foi alterado inesperadamente.")

    print()
    print("=" * 72)
    print("3. RESET")
    print("=" * 72)

    print()
    print("@PJL RESET")

    pjl.executar(
        "@PJL RESET",
        espera=0.30,
    )

    corrente_final = inquire(pjl, variavel)
    default_final = dinquire(pjl, variavel)

    print()
    print("Após RESET:")
    print(f"INQUIRE  : {corrente_final}")
    print(f"DINQUIRE : {default_final}")

    print()
    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    print()
    print(f"Original corrente : {corrente_original}")
    print(f"Original default  : {default_original}")
    print()
    print(f"Após SET corrente : {corrente_apos_set}")
    print(f"Após SET default  : {default_apos_set}")
    print()
    print(f"Após RESET corrente : {corrente_final}")
    print(f"Após RESET default  : {default_final}")

    sucesso_set = (
        corrente_apos_set == valor_teste
        and default_apos_set == default_original
    )

    sucesso_reset = (
        corrente_final == default_original
        and default_final == default_original
    )

    print()

    if sucesso_set:
        print("✓ PAPER: SET CONFIRMADO.")
    else:
        print("✗ PAPER: SET NÃO CONFIRMADO.")

    if sucesso_reset:
        print("✓ PAPER: RESET CONFIRMADO.")
    else:
        print("✗ PAPER: RESET NÃO CONFIRMADO.")

    print()

    if sucesso_set and sucesso_reset:
        print(
            "✓ PAPER pode ser manipulado no ambiente corrente "
            "sem alterar o DEFAULT."
        )
        print(
            "✓ RESET devolve PAPER ao DEFAULT."
        )
    else:
        print(
            "⚠ O comportamento de PAPER precisa de investigação adicional."
        )

    print()
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum job foi enviado.")
    print()
    print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()