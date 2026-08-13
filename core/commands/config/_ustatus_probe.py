import socket
import time


HOST_PORT = 9100
CONNECT_TIMEOUT = 3.0
RECV_TIMEOUT = 5.0
MAX_RETRIES = 3


def conectar(ip):
    ultimo_erro = None

    for tentativa in range(1, MAX_RETRIES + 1):
        print(
            f"Conectando em {ip}:{HOST_PORT} "
            f"(tentativa {tentativa}/{MAX_RETRIES})..."
        )

        try:
            sock = socket.create_connection(
                (ip, HOST_PORT),
                timeout=CONNECT_TIMEOUT,
            )

            sock.settimeout(RECV_TIMEOUT)

            print("Conectado.")
            return sock

        except (socket.timeout, OSError) as erro:
            ultimo_erro = erro

            if tentativa < MAX_RETRIES:
                time.sleep(0.5)

    raise ConnectionError(
        f"Não foi possível conectar em "
        f"{ip}:{HOST_PORT}: {ultimo_erro}"
    )


def enviar(sock, comando):
    payload = (
        comando.rstrip("\r\n") + "\r\n"
    ).encode("ascii")

    sock.sendall(payload)


def receber(sock, segundos=5.0):
    inicio = time.perf_counter()

    dados = bytearray()

    while time.perf_counter() - inicio < segundos:
        try:
            bloco = sock.recv(4096)

            if not bloco:
                break

            dados.extend(bloco)

        except socket.timeout:
            break

    return bytes(dados)


def limpar_resposta(dados):
    if not dados:
        return ""

    texto = dados.decode(
        "latin-1",
        errors="replace",
    )

    texto = texto.replace("\x00", "")

    return texto.strip()


def enviar_ustatus(sock, modo, valor):
    print()
    print("-" * 72)
    print(f"USTATUS {modo} {valor}")
    print("-" * 72)

    comando = f"@PJL USTATUS {modo} {valor}"

    enviar(sock, comando)

    print("Comando enviado.")


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 USTATUS PROBE")
    print("=" * 72)

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {HOST_PORT}")
    print()

    print("Este teste:")
    print()
    print("- NÃO altera DEFAULT.")
    print("- NÃO executa RESET.")
    print("- NÃO altera PAPER.")
    print("- NÃO altera DUPLEX.")
    print("- NÃO altera COPIES.")
    print("- NÃO altera RESOLUTION.")
    print("- NÃO altera DENSITY.")
    print("- NÃO altera ORIENTATION.")
    print()
    print("Ele somente habilita temporariamente")
    print("USTATUS nesta conexão RAW e observa")
    print("os eventos produzidos durante um job.")
    print()
    print("IMPORTANTE:")
    print()
    print("Depois que este programa iniciar a captura,")
    print("você deverá enviar um job simples para a")
    print("impressora a partir de OUTRO lugar.")
    print()
    print("Pode ser uma impressão normal de 1 página.")
    print()

    continuar = input("Continuar? [S/N]: ").strip().upper()

    if continuar != "S":
        print("Teste cancelado.")
        return

    sock = None

    try:
        sock = conectar(ip)

        print()
        print("=" * 72)
        print("1. HABILITANDO USTATUS")
        print("=" * 72)

        # Habilita eventos de dispositivo.
        enviar_ustatus(
            sock,
            "DEVICE",
            "ON",
        )

        # Habilita eventos de job.
        enviar_ustatus(
            sock,
            "JOB",
            "ON",
        )

        # Habilita eventos de página.
        enviar_ustatus(
            sock,
            "PAGE",
            "ON",
        )

        print()
        print("=" * 72)
        print("2. CAPTURA ATIVA")
        print("=" * 72)

        print()
        print("A conexão RAW está aberta.")
        print()
        print(">>> AGORA ENVIE UM JOB DE 1 PÁGINA <<<")
        print()
        print("Depois aguarde alguns segundos.")
        print()
        print("Pressione ENTER quando o job terminar.")
        print()

        input()

        print()
        print("=" * 72)
        print("3. CAPTURANDO EVENTOS")
        print("=" * 72)

        dados = receber(
            sock,
            segundos=5.0,
        )

        resposta = limpar_resposta(dados)

        print()

        if resposta:
            print(resposta)
        else:
            print("(nenhum evento recebido)")

        print()
        print("=" * 72)
        print("4. ENCERRANDO USTATUS")
        print("=" * 72)

        # Desabilita os eventos nesta conexão.
        enviar_ustatus(
            sock,
            "PAGE",
            "OFF",
        )

        enviar_ustatus(
            sock,
            "JOB",
            "OFF",
        )

        enviar_ustatus(
            sock,
            "DEVICE",
            "OFF",
        )

        print()
        print("USTATUS desabilitado.")

        print()
        print("=" * 72)
        print("5. RESULTADO")
        print("=" * 72)

        if resposta:
            print()
            print(">>> EVENTOS USTATUS RECEBIDOS <<<")
            print()
            print(resposta)
        else:
            print()
            print("Nenhum evento foi capturado.")

        print()
        print("A captura foi encerrada.")
        print("Nenhuma configuração permanente foi alterada.")

    except Exception as erro:
        print()
        print("=" * 72)
        print("ERRO")
        print("=" * 72)
        print()
        print(erro)

    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

        print()
        print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()