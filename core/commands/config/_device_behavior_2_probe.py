import socket
import time


PRINTER_DEFAULT_IP = "192.168.14.134"
RAW_PORT = 9100
TIMEOUT = 3.0
CONNECT_RETRIES = 3


VARIABLES = [
    ("PERSONALITY", "PCL"),
    ("POWERSAVE", "OFF"),
    ("POWERSAVETIME", "15"),
    ("ECONOMODE", "OFF"),
    ("PAGEPROTECT", "OFF"),
    ("RESOURCESAVE", "OFF"),
    ("WIDEA4", "OFF"),
]


def conectar(ip):
    ultimo_erro = None

    for tentativa in range(1, CONNECT_RETRIES + 1):
        print(
            f"Conectando em {ip}:{RAW_PORT} "
            f"(tentativa {tentativa}/{CONNECT_RETRIES})..."
        )

        try:
            sock = socket.create_connection(
                (ip, RAW_PORT),
                timeout=TIMEOUT,
            )
            sock.settimeout(TIMEOUT)
            print("Conectado.")
            return sock

        except Exception as exc:
            ultimo_erro = exc
            time.sleep(0.2)

    raise RuntimeError(
        f"Não foi possível conectar em {ip}:{RAW_PORT}: {ultimo_erro}"
    )


def enviar_comando(ip, comando, esperar_resposta=True):
    inicio = time.perf_counter()

    sock = conectar(ip)

    try:
        dados = (comando + "\r\n").encode("ascii")
        sock.sendall(dados)

        if not esperar_resposta:
            return None, time.perf_counter() - inicio

        resposta = b""

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta += bloco

                if b"\x0c" in bloco:
                    break

            except socket.timeout:
                break

        texto = resposta.decode(
            "latin-1",
            errors="replace",
        ).strip()

        return texto, time.perf_counter() - inicio

    finally:
        sock.close()


def inquire(ip, variavel):
    resposta, tempo = enviar_comando(
        ip,
        f"@PJL INQUIRE {variavel}",
        esperar_resposta=True,
    )

    if resposta is None:
        return None, tempo

    linhas = [
        linha.strip()
        for linha in resposta.splitlines()
        if linha.strip()
    ]

    if not linhas:
        return None, tempo

    valor = linhas[-1]

    if valor.startswith("@PJL"):
        return None, tempo

    return valor, tempo


def dinquire(ip, variavel):
    resposta, tempo = enviar_comando(
        ip,
        f"@PJL DINQUIRE {variavel}",
        esperar_resposta=True,
    )

    if resposta is None:
        return None, tempo

    linhas = [
        linha.strip()
        for linha in resposta.splitlines()
        if linha.strip()
    ]

    if not linhas:
        return None, tempo

    valor = linhas[-1]

    if valor.startswith("@PJL"):
        return None, tempo

    return valor, tempo


def set_variavel(ip, variavel, valor):
    inicio = time.perf_counter()

    comando = f"@PJL SET {variavel}={valor}"

    enviar_comando(
        ip,
        comando,
        esperar_resposta=False,
    )

    return time.perf_counter() - inicio


def reset(ip):
    inicio = time.perf_counter()

    enviar_comando(
        ip,
        "@PJL RESET",
        esperar_resposta=False,
    )

    return time.perf_counter() - inicio


def estado(ip, variavel):
    corrente, tempo_inq = inquire(ip, variavel)
    padrao, tempo_dinq = dinquire(ip, variavel)

    return {
        "current": corrente,
        "default": padrao,
        "inq_time": tempo_inq,
        "dinq_time": tempo_dinq,
    }


def confirmar_set(original, depois, valor):
    if depois["current"] == valor:
        return True

    return False


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 DEVICE BEHAVIOR 2 PROBE")
    print("=" * 72)

    ip = input(
        f"Digite o IP da impressora [{PRINTER_DEFAULT_IP}]: "
    ).strip()

    if not ip:
        ip = PRINTER_DEFAULT_IP

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {RAW_PORT}")
    print()

    print("Este teste:")
    print()
    print("- testa variáveis fora do bloco de papel;")
    print("- executa SET temporário;")
    print("- verifica INQUIRE;")
    print("- verifica DINQUIRE;")
    print("- executa RESET;")
    print("- confirma restauração;")
    print("- NÃO altera DEFAULT;")
    print("- NÃO envia nenhum job;")
    print("- NÃO imprime nenhuma página.")
    print()

    print("Variáveis que serão investigadas:")
    print()

    for variavel, valor in VARIABLES:
        print(f"- {variavel}: {valor}")

    print()

    continuar = input("Continuar? [S/N]: ").strip().upper()

    if continuar != "S":
        print("Teste cancelado.")
        return

    resultados = []

    for variavel, valor_teste in VARIABLES:
        print()
        print("=" * 72)
        print(f"VARIÁVEL: {variavel}")
        print("=" * 72)

        print()
        print("1. ESTADO ORIGINAL")
        print()

        original = estado(ip, variavel)

        print(f"INQUIRE  : {original['current']}")
        print(f"DINQUIRE : {original['default']}")

        print()
        print(f"2. SET {variavel}={valor_teste}")
        print()

        tempo_set = set_variavel(
            ip,
            variavel,
            valor_teste,
        )

        print(f"SET enviado em {tempo_set:.3f}s")

        print()
        print("Estado após SET:")
        print()

        depois_set = estado(ip, variavel)

        print(f"INQUIRE  : {depois_set['current']}")
        print(f"DINQUIRE : {depois_set['default']}")

        set_ok = confirmar_set(
            original,
            depois_set,
            valor_teste,
        )

        if set_ok:
            print(
                f"✓ SET {variavel}={valor_teste} "
                "alterou o ambiente corrente."
            )
        else:
            print(
                f"✗ SET {variavel}={valor_teste} "
                "não foi confirmado."
            )

        if (
            original["default"]
            == depois_set["default"]
        ):
            print("✓ DEFAULT permaneceu inalterado.")
        else:
            print("✗ DEFAULT foi alterado!")

        print()
        print("3. RESET")
        print()

        tempo_reset = reset(ip)

        print(f"RESET enviado em {tempo_reset:.3f}s")

        print()
        print("Estado após RESET:")
        print()

        depois_reset = estado(ip, variavel)

        print(f"INQUIRE  : {depois_reset['current']}")
        print(f"DINQUIRE : {depois_reset['default']}")

        reset_ok = (
            depois_reset["current"]
            == original["current"]
            and
            depois_reset["default"]
            == original["default"]
        )

        if reset_ok:
            print(
                "✓ RESET devolveu o ambiente "
                "ao estado original."
            )
        else:
            print(
                "✗ RESET não restaurou "
                "exatamente o estado original."
            )

        default_ok = (
            depois_set["default"]
            == original["default"]
            and
            depois_reset["default"]
            == original["default"]
        )

        if default_ok:
            print("✓ DEFAULT continua preservado.")
        else:
            print("✗ DEFAULT sofreu alteração.")

        resultados.append(
            {
                "variavel": variavel,
                "valor_teste": valor_teste,
                "original_current": original["current"],
                "original_default": original["default"],
                "after_set_current": depois_set["current"],
                "after_set_default": depois_set["default"],
                "after_reset_current": depois_reset["current"],
                "after_reset_default": depois_reset["default"],
                "set_ok": set_ok,
                "reset_ok": reset_ok,
                "default_ok": default_ok,
            }
        )

    print()
    print("=" * 72)
    print("RESUMO")
    print("=" * 72)
    print()

    print(
        f"{'VARIÁVEL':<16}"
        f"{'SET':<8}"
        f"{'RESET':<8}"
        f"{'DEFAULT':<10}"
    )

    print("-" * 72)

    for resultado in resultados:
        set_status = "✓" if resultado["set_ok"] else "✗"
        reset_status = "✓" if resultado["reset_ok"] else "✗"
        default_status = "✓" if resultado["default_ok"] else "✗"

        print(
            f"{resultado['variavel']:<16}"
            f"{set_status:<8}"
            f"{reset_status:<8}"
            f"{default_status:<10}"
        )

    total = len(resultados)

    sets_ok = sum(
        1
        for resultado in resultados
        if resultado["set_ok"]
    )

    resets_ok = sum(
        1
        for resultado in resultados
        if resultado["reset_ok"]
    )

    defaults_ok = sum(
        1
        for resultado in resultados
        if resultado["default_ok"]
    )

    print()
    print(f"Variáveis testadas  : {total}")
    print(f"SET confirmados     : {sets_ok}/{total}")
    print(f"RESET confirmados   : {resets_ok}/{total}")
    print(f"DEFAULT preservado  : {defaults_ok}/{total}")
    print()

    print("Nenhum job foi enviado.")
    print("Nenhuma página deveria ter sido impressa.")
    print()
    print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()