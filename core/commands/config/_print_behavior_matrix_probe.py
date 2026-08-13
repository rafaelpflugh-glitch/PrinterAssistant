import socket
import time


HOST = "192.168.14.134"
PORT = 9100

TIMEOUT = 3
RETRIES = 3


# ============================================================
# CONEXÃO RAW
# ============================================================

def conectar():
    ultimo_erro = None

    for tentativa in range(1, RETRIES + 1):
        print(
            f"Conectando em {HOST}:{PORT} "
            f"(tentativa {tentativa}/{RETRIES})..."
        )

        try:
            sock = socket.create_connection(
                (HOST, PORT),
                timeout=TIMEOUT
            )

            sock.settimeout(TIMEOUT)
            print("Conectado.")
            return sock

        except Exception as erro:
            ultimo_erro = erro
            time.sleep(0.3)

    raise ConnectionError(
        f"Não foi possível conectar em {HOST}:{PORT}: {ultimo_erro}"
    )


# ============================================================
# ENVIO RAW
# ============================================================

def enviar_raw(dados):
    sock = conectar()

    try:
        inicio = time.perf_counter()

        sock.sendall(dados)

        tempo = time.perf_counter() - inicio

        return len(dados), tempo

    finally:
        sock.close()


# ============================================================
# PJL
# ============================================================

def pjl_comando(comando):
    return (
        f"\x1b%-12345X"
        f"@PJL {comando}\r\n"
    ).encode("ascii")


def pjl_job_prefix():
    return (
        b"\x1b%-12345X"
        b"@PJL JOB NAME=\"PRINTER_ASSISTANT_MATRIX\"\r\n"
    )


def pjl_job_suffix():
    return (
        b"\x1b%-12345X"
    )


# ============================================================
# INQUIRE
# ============================================================

def inquire(variavel):
    dados = (
        b"\x1b%-12345X"
        + f"@PJL INQUIRE {variavel}\r\n".encode("ascii")
        + b"\x1b%-12345X"
    )

    sock = conectar()

    try:
        inicio = time.perf_counter()

        sock.sendall(dados)

        resposta = b""

        try:
            while True:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta += bloco

                if b"\r\n" in resposta:
                    break

        except socket.timeout:
            pass

        tempo = time.perf_counter() - inicio

    finally:
        sock.close()

    texto = resposta.decode(
        "ascii",
        errors="replace"
    ).strip()

    return texto, tempo


def dinquire(variavel):
    dados = (
        b"\x1b%-12345X"
        + f"@PJL DINQUIRE {variavel}\r\n".encode("ascii")
        + b"\x1b%-12345X"
    )

    sock = conectar()

    try:
        inicio = time.perf_counter()

        sock.sendall(dados)

        resposta = b""

        try:
            while True:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta += bloco

                if b"\r\n" in resposta:
                    break

        except socket.timeout:
            pass

        tempo = time.perf_counter() - inicio

    finally:
        sock.close()

    texto = resposta.decode(
        "ascii",
        errors="replace"
    ).strip()

    return texto, tempo


# ============================================================
# LEITURA DO ESTADO
# ============================================================

def ler_estado(variavel):
    atual, _ = inquire(variavel)
    padrao, _ = dinquire(variavel)

    return atual, padrao


def mostrar_estado(variavel):
    atual, padrao = ler_estado(variavel)

    print(f"INQUIRE  : {atual}")
    print(f"DINQUIRE : {padrao}")

    return atual, padrao


# ============================================================
# SET
# ============================================================

def set_variavel(variavel, valor):
    dados = pjl_comando(
        f"SET {variavel}={valor}"
    )

    inicio = time.perf_counter()

    enviar_raw(dados)

    tempo = time.perf_counter() - inicio

    return tempo


# ============================================================
# RESET
# ============================================================

def reset():
    dados = pjl_comando("RESET")

    inicio = time.perf_counter()

    enviar_raw(dados)

    tempo = time.perf_counter() - inicio

    return tempo


# ============================================================
# PCL
# ============================================================

def pcl_texto(texto):
    return texto.encode("ascii", errors="replace")


def pcl_job(pagina1, pagina2):
    pcl = bytearray()

    # Reset PCL
    pcl += b"\x1bE"

    # Margem/origem padrão
    pcl += b"\x1b&l0E"

    # Texto simples
    pcl += pcl_texto(pagina1)

    # Nova página
    pcl += b"\x0c"

    pcl += pcl_texto(pagina2)

    # Finaliza página
    pcl += b"\x0c"

    return bytes(pcl)


# ============================================================
# JOB
# ============================================================

def enviar_job(variavel, valor, pagina1, pagina2):
    prefixo = (
        b"\x1b%-12345X"
        + f"@PJL SET {variavel}={valor}\r\n".encode("ascii")
        + b"@PJL ENTER LANGUAGE=PCL\r\n"
    )

    pcl = pcl_job(
        pagina1,
        pagina2
    )

    suffixo = (
        b"\x1b%-12345X"
    )

    job = prefixo + pcl + suffixo

    inicio = time.perf_counter()

    sock = conectar()

    try:
        sock.sendall(job)
    finally:
        sock.close()

    tempo = time.perf_counter() - inicio

    return len(job), tempo


# ============================================================
# TESTE
# ============================================================

def executar_teste(
    numero,
    variavel,
    valor,
    descricao
):
    print()
    print("=" * 72)
    print(f"TESTE {numero}")
    print("=" * 72)

    print(f"Variável : {variavel}")
    print(f"SET      : {valor}")
    print(f"Objetivo : {descricao}")
    print()

    print("1. ESTADO ORIGINAL")
    print("-" * 72)

    original_atual, original_default = mostrar_estado(
        variavel
    )

    print()
    print(f"2. SET {variavel}={valor}")
    print("-" * 72)

    tempo_set = set_variavel(
        variavel,
        valor
    )

    print(f"SET enviado em {tempo_set:.3f}s")

    print()
    print("Estado após SET:")

    apos_set_atual, apos_set_default = mostrar_estado(
        variavel
    )

    print()

    if str(apos_set_atual).upper() == str(valor).upper():
        print(
            f"✓ SET {variavel}={valor} alterou "
            f"o ambiente corrente."
        )
    else:
        print(
            f"✗ SET {variavel}={valor} "
            f"não produziu o valor esperado."
        )

    if (
        str(apos_set_default).upper()
        == str(original_default).upper()
    ):
        print("✓ DEFAULT permaneceu inalterado.")
    else:
        print(
            "✗ DEFAULT foi alterado!"
        )

    print()
    print("3. JOB PCL")
    print("-" * 72)

    pagina1 = (
        f"PRINTER ASSISTANT\r\n"
        f"TESTE {numero}\r\n"
        f"{variavel}={valor}\r\n"
        f"PAGINA 1\r\n"
    )

    pagina2 = (
        f"PRINTER ASSISTANT\r\n"
        f"TESTE {numero}\r\n"
        f"{variavel}={valor}\r\n"
        f"PAGINA 2\r\n"
    )

    print(
        "O job contém duas páginas dentro do mesmo job."
    )

    print(
        "Observe fisicamente o comportamento da impressora."
    )

    input(
        "Pressione ENTER para enviar o job..."
    )

    bytes_enviados, tempo_job = enviar_job(
        variavel,
        valor,
        pagina1,
        pagina2
    )

    print()
    print("Job enviado.")
    print(f"Bytes enviados: {bytes_enviados}")
    print(f"Tempo:          {tempo_job:.3f}s")

    print()
    print("Observe:")
    print("- número de folhas")
    print("- número de páginas")
    print("- orientação")
    print("- duplex")
    print("- qualidade aparente")
    print("- comportamento geral")

    input(
        "Pressione ENTER para executar RESET..."
    )

    print()
    print("4. RESET")
    print("-" * 72)

    tempo_reset = reset()

    print(
        f"RESET enviado em {tempo_reset:.3f}s"
    )

    print()
    print("Estado após RESET:")

    final_atual, final_default = mostrar_estado(
        variavel
    )

    print()
    print("5. RESULTADO")
    print("-" * 72)

    print(
        f"Original corrente   : {original_atual}"
    )

    print(
        f"Original default    : {original_default}"
    )

    print(
        f"Após SET corrente   : {apos_set_atual}"
    )

    print(
        f"Após SET default    : {apos_set_default}"
    )

    print(
        f"Após RESET corrente : {final_atual}"
    )

    print(
        f"Após RESET default  : {final_default}"
    )

    if (
        str(final_atual).upper()
        == str(original_atual).upper()
        and
        str(final_default).upper()
        == str(original_default).upper()
    ):
        print()
        print(
            "✓ RESET restaurou o estado original."
        )
    else:
        print()
        print(
            "✗ ESTADO FINAL DIFERE DO ORIGINAL."
        )

    return {
        "variavel": variavel,
        "valor": valor,
        "original_atual": original_atual,
        "original_default": original_default,
        "apos_set_atual": apos_set_atual,
        "apos_set_default": apos_set_default,
        "final_atual": final_atual,
        "final_default": final_default,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 PRINT BEHAVIOR MATRIX PROBE")
    print("=" * 72)

    print()
    print(f"Impressora: {HOST}")
    print(f"RAW:        {PORT}")

    print()
    print("Este teste:")
    print()
    print("- NÃO altera DEFAULT.")
    print("- altera somente o ambiente corrente.")
    print("- envia jobs PCL controlados.")
    print("- executa RESET após cada teste.")
    print("- confirma a restauração.")
    print()

    print("Variáveis investigadas:")

    testes = [
        (
            "RESOLUTION",
            "1200",
            "verificar se a resolução PJL altera fisicamente o job"
        ),
        (
            "DENSITY",
            "4",
            "verificar se a densidade PJL altera fisicamente o job"
        ),
        (
            "COPIES",
            "2",
            "verificar cópias múltiplas dentro do job"
        ),
        (
            "ORIENTATION",
            "LANDSCAPE",
            "verificar orientação PJL no job"
        ),
        (
            "DUPLEX",
            "ON",
            "verificar duplex PJL no job"
        ),
    ]

    for variavel, valor, descricao in testes:
        print(
            f"- {variavel}={valor}"
        )

    print()
    resposta = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if resposta != "S":
        print("Teste cancelado.")
        return

    resultados = []

    for numero, (variavel, valor, descricao) in enumerate(
        testes,
        start=1
    ):
        resultado = executar_teste(
            numero,
            variavel,
            valor,
            descricao
        )

        resultados.append(resultado)

    print()
    print("=" * 72)
    print("RESUMO")
    print("=" * 72)

    print()

    print(
        f"{'VARIAVEL':<15}"
        f"{'SET':<10}"
        f"{'RESET':<10}"
        f"{'DEFAULT':<10}"
    )

    print("-" * 50)

    for resultado in resultados:
        variavel = resultado["variavel"]

        set_ok = (
            str(resultado["apos_set_atual"]).upper()
            == str(resultado["valor"]).upper()
        )

        reset_ok = (
            str(resultado["final_atual"]).upper()
            == str(resultado["original_atual"]).upper()
        )

        default_ok = (
            str(resultado["final_default"]).upper()
            == str(resultado["original_default"]).upper()
        )

        print(
            f"{variavel:<15}"
            f"{'✓' if set_ok else '✗':<10}"
            f"{'✓' if reset_ok else '✗':<10}"
            f"{'✓' if default_ok else '✗':<10}"
        )

    print()
    print("Todos os testes foram finalizados.")
    print("Nenhum DEFAULT foi alterado.")
    print("O ambiente corrente foi restaurado com RESET.")


if __name__ == "__main__":
    main()