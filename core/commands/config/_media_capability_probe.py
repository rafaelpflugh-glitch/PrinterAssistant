"""
Printer Assistant - PJL Media Capability Probe

Investiga variaveis relacionadas a midia.

Este modulo:
- nao altera configuracoes;
- nao executa SET;
- nao executa DEFAULT;
- nao executa RESET;
- nao envia jobs.
"""

import socket
import time


class PJLConnection:
    def __init__(self, ip, port=9100, timeout=3, retries=3):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.retries = retries

    def send(self, command, wait=0.25):
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

                time.sleep(wait)

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


def limpar_resposta(resposta):
    if resposta is None:
        return ""

    resposta = (
        resposta
        .replace("\x00", "")
        .replace("\x0c", "")
        .replace("\x1b", "")
        .strip()
    )

    linhas = []

    for linha in resposta.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        if linha.startswith("@PJL"):
            continue

        linhas.append(linha)

    return "\n".join(linhas)


def consultar(connection, comando):
    try:
        resposta_bruta = connection.send(comando)
    except Exception as exc:
        return {
            "comando": comando,
            "valor": "",
            "resposta_bruta": "",
            "erro": str(exc),
        }

    valor = limpar_resposta(resposta_bruta)

    return {
        "comando": comando,
        "valor": valor,
        "resposta_bruta": resposta_bruta.strip(),
        "erro": None,
    }


def imprimir_consulta(nome, inquire, dinquire):
    print()
    print("-" * 72)
    print(nome)
    print("-" * 72)

    if inquire["erro"]:
        print(f"INQUIRE  : ERRO - {inquire['erro']}")
    elif inquire["valor"]:
        print(f"INQUIRE  : {inquire['valor']}")
    else:
        print("INQUIRE  : (sem resposta)")

    if dinquire["erro"]:
        print(f"DINQUIRE : ERRO - {dinquire['erro']}")
    elif dinquire["valor"]:
        print(f"DINQUIRE : {dinquire['valor']}")
    else:
        print("DINQUIRE : (sem resposta)")


def consultar_variavel(connection, nome):
    inquire = consultar(
        connection,
        f"@PJL INQUIRE {nome}",
    )

    dinquire = consultar(
        connection,
        f"@PJL DINQUIRE {nome}",
    )

    imprimir_consulta(
        nome,
        inquire,
        dinquire,
    )

    return {
        "nome": nome,
        "inquire": inquire,
        "dinquire": dinquire,
    }


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL MEDIA CAPABILITY PROBE")
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP invalido.")
        return

    print()
    print(f"Impressora: {ip}")
    print("RAW:        9100")
    print()
    print("Este teste:")
    print()
    print("- NAO altera PAPER.")
    print("- NAO altera MEDIATYPE.")
    print("- NAO executa SET.")
    print("- NAO executa DEFAULT.")
    print("- NAO executa RESET.")
    print("- NAO envia jobs.")
    print()
    print(
        "Serão apenas consultadas informacoes "
        "da impressora."
    )
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
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
    print("1. IDENTIDADE")
    print("=" * 72)

    identidade = connection.send(
        "@PJL INFO ID"
    ).strip()

    print(identidade or "(sem resposta)")

    print()
    print("=" * 72)
    print("2. INFO CONFIG")
    print("=" * 72)

    config = connection.send(
        "@PJL INFO CONFIG"
    ).strip()

    print(config or "(sem resposta)")

    print()
    print("=" * 72)
    print("3. PAPER")
    print("=" * 72)

    consultar_variavel(
        connection,
        "PAPER",
    )

    print()
    print("=" * 72)
    print("4. MEDIATYPE")
    print("=" * 72)

    consultar_variavel(
        connection,
        "MEDIATYPE",
    )

    print()
    print("=" * 72)
    print("5. VARIAVEIS RELACIONADAS A MIDIA")
    print("=" * 72)

    variaveis = [
        "MEDIAWEIGHT",
        "MEDIATEXTURE",
        "PAPERWEIGHT",
        "PAPERFINISH",
        "PAPERTYPE",
        "TRAY1",
        "TRAY2",
        "TRAY3",
        "TRAY4",
        "TRAY5",
    ]

    resultados = []

    for variavel in variaveis:
        resultado = consultar_variavel(
            connection,
            variavel,
        )

        resultados.append(resultado)

    print()
    print("=" * 72)
    print("6. RESUMO")
    print("=" * 72)

    for resultado in resultados:
        nome = resultado["nome"]

        corrente = resultado["inquire"]["valor"]
        padrao = resultado["dinquire"]["valor"]

        if not corrente:
            corrente = "(sem resposta)"

        if not padrao:
            padrao = "(sem resposta)"

        print(
            f"{nome:15} "
            f"CURRENT={corrente:20} "
            f"DEFAULT={padrao}"
        )

    print()
    print("=" * 72)
    print("FIM DA DESCOBERTA")
    print("=" * 72)
    print()
    print("Nenhuma configuracao foi alterada.")
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum job foi enviado.")
    print()


if __name__ == "__main__":
    main()