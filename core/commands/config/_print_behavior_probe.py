import socket
import time
import re


RAW_PORT = 9100
CONNECT_TIMEOUT = 3.0
READ_TIMEOUT = 2.0
RETRIES = 3


def conectar(ip):
    ultimo_erro = None

    for tentativa in range(1, RETRIES + 1):
        try:
            print(
                f"Conectando em {ip}:{RAW_PORT} "
                f"(tentativa {tentativa}/{RETRIES})..."
            )

            sock = socket.create_connection(
                (ip, RAW_PORT),
                timeout=CONNECT_TIMEOUT,
            )

            sock.settimeout(READ_TIMEOUT)
            print("Conectado.")
            return sock

        except Exception as exc:
            ultimo_erro = exc
            time.sleep(0.25)

    raise ultimo_erro


def enviar(ip, comando, esperar=0.5):
    sock = conectar(ip)

    try:
        if not comando.endswith("\n"):
            comando += "\n"

        sock.sendall(comando.encode("ascii", errors="replace"))

        time.sleep(esperar)

        dados = b""

        while True:
            try:
                parte = sock.recv(4096)

                if not parte:
                    break

                dados += parte

            except socket.timeout:
                break

        return dados.decode("latin-1", errors="replace")

    finally:
        sock.close()


def limpar_resposta(texto):
    if not texto:
        return None

    texto = texto.replace("\r", "")
    linhas = [x.strip() for x in texto.split("\n") if x.strip()]

    if not linhas:
        return None

    resultados = []

    for linha in linhas:
        if linha.startswith("@PJL"):
            continue

        resultados.append(linha)

    if not resultados:
        return None

    return resultados[-1]


def inquire(ip, variavel):
    resposta = enviar(
        ip,
        f"@PJL INQUIRE {variavel}",
        esperar=0.35,
    )

    return limpar_resposta(resposta)


def dinquire(ip, variavel):
    resposta = enviar(
        ip,
        f"@PJL DINQUIRE {variavel}",
        esperar=0.35,
    )

    return limpar_resposta(resposta)


def set_variavel(ip, variavel, valor):
    enviar(
        ip,
        f"@PJL SET {variavel}={valor}",
        esperar=0.25,
    )


def reset(ip):
    enviar(
        ip,
        "@PJL RESET",
        esperar=0.5,
    )


def testar_variavel(ip, variavel, valor_teste):
    print()
    print("=" * 72)
    print(f"VARIÁVEL: {variavel}")
    print("=" * 72)

    print()
    print("1. ESTADO ORIGINAL")
    print("-" * 72)

    original_corrente = inquire(ip, variavel)
    original_default = dinquire(ip, variavel)

    print(f"INQUIRE  : {original_corrente}")
    print(f"DINQUIRE : {original_default}")

    print()
    print(f"2. SET {variavel}={valor_teste}")
    print("-" * 72)

    inicio = time.perf_counter()

    try:
        set_variavel(ip, variavel, valor_teste)
        tempo_set = time.perf_counter() - inicio
    except Exception as exc:
        tempo_set = time.perf_counter() - inicio
        print(f"Erro no SET: {exc}")
        return {
            "variavel": variavel,
            "set": False,
            "reset": False,
            "default_preservado": False,
        }

    print(f"SET enviado em {tempo_set:.3f}s")

    time.sleep(0.3)

    depois_set_corrente = inquire(ip, variavel)
    depois_set_default = dinquire(ip, variavel)

    print()
    print("Estado após SET:")
    print(f"INQUIRE  : {depois_set_corrente}")
    print(f"DINQUIRE : {depois_set_default}")

    set_ok = (
        depois_set_corrente is not None
        and depois_set_corrente.upper() == str(valor_teste).upper()
    )

    default_ok = (
        depois_set_default == original_default
    )

    if set_ok:
        print(f"✓ SET {variavel} alterou o ambiente corrente.")
    else:
        print(
            f"✗ SET {variavel} não produziu "
            f"o valor esperado."
        )

    if default_ok:
        print("✓ DEFAULT permaneceu inalterado.")
    else:
        print("✗ DEFAULT mudou!")

    print()
    print("3. RESET")
    print("-" * 72)

    inicio = time.perf_counter()

    try:
        reset(ip)
        tempo_reset = time.perf_counter() - inicio
    except Exception as exc:
        tempo_reset = time.perf_counter() - inicio
        print(f"Erro no RESET: {exc}")
        return {
            "variavel": variavel,
            "set": set_ok,
            "reset": False,
            "default_preservado": default_ok,
        }

    print(f"RESET enviado em {tempo_reset:.3f}s")

    time.sleep(0.3)

    depois_reset_corrente = inquire(ip, variavel)
    depois_reset_default = dinquire(ip, variavel)

    print()
    print("Estado após RESET:")
    print(f"INQUIRE  : {depois_reset_corrente}")
    print(f"DINQUIRE : {depois_reset_default}")

    reset_ok = (
        depois_reset_corrente == original_corrente
        and depois_reset_default == original_default
    )

    if reset_ok:
        print("✓ RESET devolveu o ambiente ao estado original.")
    else:
        print("✗ RESET não restaurou exatamente o estado original.")

    if depois_reset_default == original_default:
        print("✓ DEFAULT continua preservado.")
    else:
        print("✗ DEFAULT foi alterado!")

    return {
        "variavel": variavel,
        "set": set_ok,
        "reset": reset_ok,
        "default_preservado": (
            depois_reset_default == original_default
        ),
    }


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 PRINT BEHAVIOR PROBE")
    print("=" * 72)

    ip = input("Digite o IP da impressora: ").strip()

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {RAW_PORT}")
    print()

    print("Este teste:")
    print()
    print("- NÃO envia jobs.")
    print("- NÃO imprime páginas.")
    print("- NÃO altera DEFAULT.")
    print("- usa somente SET temporário.")
    print("- verifica INQUIRE.")
    print("- verifica DINQUIRE.")
    print("- executa RESET.")
    print("- confirma restauração.")
    print()

    testes = [
        ("ECONOMODE", "ON"),
        ("PAGEPROTECT", "ON"),
        ("MANUALFEED", "ON"),
        ("MPTRAY", "ON"),
        ("WIDEA4", "ON"),
        ("POWERSAVE", "ON"),
        ("RESOURCESAVE", "ON"),
        ("REPRINT", "ON"),
    ]

    print("Variáveis que serão investigadas:")
    print()

    for variavel, valor in testes:
        print(f"- {variavel} = {valor}")

    print()
    confirma = input("Continuar? [S/N]: ").strip().upper()

    if confirma != "S":
        print("Teste cancelado.")
        return

    resultados = []

    for variavel, valor in testes:
        try:
            resultado = testar_variavel(
                ip,
                variavel,
                valor,
            )

            resultados.append(resultado)

        except Exception as exc:
            print()
            print(f"ERRO FATAL AO TESTAR {variavel}: {exc}")

            resultados.append({
                "variavel": variavel,
                "set": False,
                "reset": False,
                "default_preservado": False,
            })

    print()
    print("=" * 72)
    print("RESUMO")
    print("=" * 72)

    print()
    print(
        f"{'VARIÁVEL':<18}"
        f"{'SET':<10}"
        f"{'RESET':<10}"
        f"{'DEFAULT':<12}"
    )

    print("-" * 52)

    for resultado in resultados:
        variavel = resultado["variavel"]

        set_status = "✓" if resultado["set"] else "✗"
        reset_status = "✓" if resultado["reset"] else "✗"
        default_status = (
            "✓"
            if resultado["default_preservado"]
            else "✗"
        )

        print(
            f"{variavel:<18}"
            f"{set_status:<10}"
            f"{reset_status:<10}"
            f"{default_status:<12}"
        )

    total = len(resultados)
    sets = sum(1 for r in resultados if r["set"])
    resets = sum(1 for r in resultados if r["reset"])
    defaults = sum(
        1
        for r in resultados
        if r["default_preservado"]
    )

    print()
    print(f"Variáveis testadas  : {total}")
    print(f"SET confirmados     : {sets}/{total}")
    print(f"RESET confirmados   : {resets}/{total}")
    print(f"DEFAULT preservado  : {defaults}/{total}")

    print()
    print("Nenhum job foi enviado.")
    print("Nenhuma página deveria ter sido impressa.")
    print()
    print("Fim do probe.")


if __name__ == "__main__":
    main()