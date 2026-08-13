import socket
import time


HOST = "192.168.14.134"
PORT = 9100
TIMEOUT = 5
RETRIES = 3


def conectar():
    ultimo_erro = None

    for tentativa in range(1, RETRIES + 1):
        try:
            print(
                f"Conectando em {HOST}:{PORT} "
                f"(tentativa {tentativa}/{RETRIES})..."
            )

            sock = socket.create_connection(
                (HOST, PORT),
                timeout=TIMEOUT,
            )

            sock.settimeout(TIMEOUT)

            print("Conectado.")
            return sock

        except Exception as erro:
            ultimo_erro = erro

            if tentativa < RETRIES:
                time.sleep(0.5)

    raise RuntimeError(
        f"Não foi possível conectar em {HOST}:{PORT}: {ultimo_erro}"
    )


def enviar_comando(comando, aguardar_resposta=True):
    sock = conectar()

    try:
        inicio = time.perf_counter()

        dados = (
            "\x1b%-12345X"
            "@PJL\r\n"
            f"{comando}\r\n"
            "\x1b%-12345X"
        ).encode("ascii", errors="replace")

        sock.sendall(dados)

        if not aguardar_resposta:
            tempo = time.perf_counter() - inicio
            return None, tempo

        resposta = bytearray()

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta.extend(bloco)

                if b"\x0c" in bloco:
                    break

            except socket.timeout:
                break

        tempo = time.perf_counter() - inicio

        texto = resposta.decode(
            "ascii",
            errors="replace",
        )

        return texto.strip(), tempo

    finally:
        try:
            sock.close()
        except Exception:
            pass


def limpar_resposta(texto):
    if texto is None:
        return None

    texto = texto.replace("\x00", "")
    texto = texto.replace("\x1b%-12345X", "")
    texto = texto.strip()

    if not texto:
        return None

    return texto


def consultar(comando):
    resposta, tempo = enviar_comando(comando)

    resposta = limpar_resposta(resposta)

    return resposta, tempo


def imprimir_bloco(titulo, comando):
    print()
    print("-" * 72)
    print(f"## {titulo}")
    print("-" * 72)

    print(f"Comando:")
    print(comando)

    resposta, tempo = consultar(comando)

    if resposta is None:
        print("Resposta : <nenhuma resposta>")
    else:
        print("Resposta :")
        print(resposta)

    print(f"Tempo    : {tempo:.3f}s")

    return resposta


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL INFO CAPABILITY PROBE")
    print("=" * 72)

    print()
    print(f"Impressora: {HOST}")
    print(f"RAW:        {PORT}")

    print()
    print("Este teste:")
    print()
    print("- NAO executa SET.")
    print("- NAO executa DEFAULT.")
    print("- NAO executa RESET.")
    print("- NAO envia jobs.")
    print("- NAO altera configuracoes.")
    print()
    print("Serão somente consultados comandos INFO PJL.")
    print()

    comandos = [
        ("INFO ID", "@PJL INFO ID"),
        ("INFO CONFIG", "@PJL INFO CONFIG"),
        ("INFO STATUS", "@PJL INFO STATUS"),
        ("INFO VARIABLES", "@PJL INFO VARIABLES"),
        ("INFO PRODINFO", "@PJL INFO PRODINFO"),
        ("INFO FILESYS", "@PJL INFO FILESYS"),
        ("INFO MEMORY", "@PJL INFO MEMORY"),
        ("INFO PAGECOUNT", "@PJL INFO PAGECOUNT"),
    ]

    resposta = input("Continuar? [S/N]: ").strip().upper()

    if resposta != "S":
        print("Teste cancelado.")
        return

    print()
    print("=" * 72)
    print("1. DESCOBERTA DE COMANDOS INFO")
    print("=" * 72)

    resultados = {}

    for titulo, comando in comandos:
        try:
            resultados[titulo] = imprimir_bloco(
                titulo,
                comando,
            )

        except Exception as erro:
            resultados[titulo] = None

            print()
            print(f"ERRO em {titulo}:")
            print(erro)

    print()
    print("=" * 72)
    print("2. RESUMO")
    print("=" * 72)

    for titulo, _ in comandos:
        resultado = resultados.get(titulo)

        if resultado:
            print(f"✓ {titulo}")
        else:
            print(f"✗ {titulo}")

    print()
    print("Nenhuma configuracao foi alterada.")
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum job foi enviado.")
    print()
    print("Os resultados devem ser preservados para")
    print("a proxima etapa de descoberta sistematica PJL.")


if __name__ == "__main__":
    main()