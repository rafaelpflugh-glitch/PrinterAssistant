import socket
import time


RAW_PORT = 9100
TIMEOUT = 3.0
RETRIES = 3


TESTES = [
    {
        "variavel": "ECONOMODE",
        "original": "OFF",
        "teste": "ON",
    },
    {
        "variavel": "POWERSAVE",
        "original": "ON",
        "teste": "OFF",
    },
    {
        "variavel": "POWERSAVETIME",
        "original": "15",
        "teste": "30",
    },
    {
        "variavel": "TIMEOUT",
        "original": "90",
        "teste": "120",
    },
    {
        "variavel": "AUTOCONT",
        "original": "5",
        "teste": "10",
    },
    {
        "variavel": "PAGEPROTECT",
        "original": "AUTO",
        "teste": "ON",
    },
    {
        "variavel": "REPRINT",
        "original": "AUTO",
        "teste": "AUTO",
    },
    {
        "variavel": "RESOURCESAVE",
        "original": "AUTO",
        "teste": "AUTO",
    },
    {
        "variavel": "WIDEA4",
        "original": "NO",
        "teste": "YES",
    },
]


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
                timeout=TIMEOUT,
            )

            sock.settimeout(TIMEOUT)

            print("Conectado.")
            return sock

        except Exception as exc:
            ultimo_erro = exc

            if tentativa < RETRIES:
                time.sleep(0.5)

    raise ultimo_erro


def enviar(ip, texto):
    sock = conectar(ip)

    try:
        dados = texto.encode("latin-1", errors="replace")

        inicio = time.perf_counter()

        sock.sendall(dados)

        tempo = time.perf_counter() - inicio

        return tempo

    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        sock.close()


def consultar(ip, comando):
    sock = conectar(ip)

    try:
        inicio = time.perf_counter()

        sock.sendall(
            f"\x1b%-12345X"
            f"@PJL {comando}\r\n"
            f"\x1b%-12345X"
            .encode("ascii")
        )

        resposta = b""

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta += bloco

                if len(bloco) < 4096:
                    break

            except socket.timeout:
                break

        tempo = time.perf_counter() - inicio

        texto = resposta.decode(
            "latin-1",
            errors="replace",
        )

        linhas = []

        for linha in texto.splitlines():
            linha = linha.strip()

            if not linha:
                continue

            if linha.startswith("@PJL"):
                continue

            if linha.startswith("\x1b"):
                continue

            linhas.append(linha)

        valor = linhas[-1] if linhas else None

        return valor, tempo

    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

        sock.close()


def inquire(ip, variavel):
    return consultar(
        ip,
        f"INQUIRE {variavel}",
    )


def dinquire(ip, variavel):
    return consultar(
        ip,
        f"DINQUIRE {variavel}",
    )


def setar(ip, variavel, valor):
    return enviar(
        ip,
        (
            "\x1b%-12345X"
            f"@PJL SET {variavel}={valor}\r\n"
            "\x1b%-12345X"
        ),
    )


def resetar(ip):
    return enviar(
        ip,
        (
            "\x1b%-12345X"
            "@PJL RESET\r\n"
            "\x1b%-12345X"
        ),
    )


def mostrar_estado(ip, variavel):
    corrente, tempo_i = inquire(ip, variavel)
    padrao, tempo_d = dinquire(ip, variavel)

    print(f"INQUIRE  : {corrente}")
    print(f"DINQUIRE : {padrao}")

    return corrente, padrao


def testar_variavel(ip, teste):
    variavel = teste["variavel"]
    valor_teste = teste["teste"]

    print()
    print("=" * 72)
    print(f"VARIAVEL: {variavel}")
    print("=" * 72)

    print()
    print("1. ESTADO ORIGINAL")
    print("-" * 72)

    original_corrente, original_default = mostrar_estado(
        ip,
        variavel,
    )

    print()
    print(f"2. SET {variavel}={valor_teste}")
    print("-" * 72)

    print(
        f"@PJL SET {variavel}={valor_teste}"
    )

    try:
        tempo_set = setar(
            ip,
            variavel,
            valor_teste,
        )

        print(
            f"SET enviado em {tempo_set:.3f}s"
        )

    except Exception as exc:
        print()
        print(
            f"✗ ERRO AO ENVIAR SET: {exc}"
        )

        return {
            "variavel": variavel,
            "original_corrente": original_corrente,
            "original_default": original_default,
            "apos_set_corrente": None,
            "apos_set_default": None,
            "apos_reset_corrente": None,
            "apos_reset_default": None,
            "set_ok": False,
            "reset_ok": False,
        }

    time.sleep(0.3)

    apos_set_corrente, apos_set_default = mostrar_estado(
        ip,
        variavel,
    )

    set_ok = (
        str(apos_set_corrente).upper()
        == str(valor_teste).upper()
    )

    default_preservado = (
        str(apos_set_default).upper()
        == str(original_default).upper()
    )

    if set_ok:
        print()
        print(
            f"✓ SET {variavel}={valor_teste} "
            "alterou o ambiente corrente."
        )
    else:
        print()
        print(
            f"✗ SET {variavel}={valor_teste} "
            "não produziu o valor esperado."
        )

    if default_preservado:
        print(
            "✓ DEFAULT permaneceu inalterado."
        )
    else:
        print(
            "✗ DEFAULT foi alterado."
        )

    print()
    print("3. RESET")
    print("-" * 72)

    try:
        tempo_reset = resetar(ip)

        print(
            f"RESET enviado em {tempo_reset:.3f}s"
        )

    except Exception as exc:
        print()
        print(
            f"✗ ERRO AO ENVIAR RESET: {exc}"
        )

        return {
            "variavel": variavel,
            "original_corrente": original_corrente,
            "original_default": original_default,
            "apos_set_corrente": apos_set_corrente,
            "apos_set_default": apos_set_default,
            "apos_reset_corrente": None,
            "apos_reset_default": None,
            "set_ok": set_ok,
            "reset_ok": False,
        }

    time.sleep(0.3)

    apos_reset_corrente, apos_reset_default = mostrar_estado(
        ip,
        variavel,
    )

    reset_ok = (
        str(apos_reset_corrente).upper()
        == str(original_corrente).upper()
        and
        str(apos_reset_default).upper()
        == str(original_default).upper()
    )

    if reset_ok:
        print()
        print(
            "✓ RESET devolveu o ambiente "
            "ao estado original."
        )
        print(
            "✓ DEFAULT continua preservado."
        )
    else:
        print()
        print(
            "✗ RESET não devolveu "
            "exatamente o estado original."
        )

    return {
        "variavel": variavel,
        "original_corrente": original_corrente,
        "original_default": original_default,
        "apos_set_corrente": apos_set_corrente,
        "apos_set_default": apos_set_default,
        "apos_reset_corrente": apos_reset_corrente,
        "apos_reset_default": apos_reset_default,
        "set_ok": set_ok,
        "default_preservado": default_preservado,
        "reset_ok": reset_ok,
    }


def main():
    print()
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - "
        "MX611 SYSTEM BEHAVIOR SET / RESET PROBE"
    )
    print("=" * 72)
    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print()
        print("IP não informado.")
        return

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {RAW_PORT}")
    print()

    print("Este teste:")
    print()
    print("- testa variáveis de comportamento do sistema;");
    print("- executa SET temporário;");
    print("- verifica INQUIRE;");
    print("- verifica DINQUIRE;");
    print("- executa RESET;");
    print("- confirma restauração;");
    print("- NÃO altera DEFAULT;");
    print("- NÃO envia nenhum job;");
    print("- NÃO imprime nenhuma página.")
    print()

    print("Variáveis que serão testadas:")
    print()

    for teste in TESTES:
        print(
            f"- {teste['variavel']}: "
            f"{teste['teste']}"
        )

    print()

    resposta = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if resposta != "S":
        print()
        print("Teste cancelado.")
        return

    resultados = []

    for teste in TESTES:
        resultado = testar_variavel(
            ip,
            teste,
        )

        resultados.append(resultado)

    print()
    print("=" * 72)
    print("RESUMO FINAL")
    print("=" * 72)
    print()

    for resultado in resultados:
        variavel = resultado["variavel"]

        set_ok = resultado.get(
            "set_ok",
            False,
        )

        reset_ok = resultado.get(
            "reset_ok",
            False,
        )

        default_ok = resultado.get(
            "default_preservado",
            False,
        )

        if set_ok:
            set_status = "✓ SET"
        else:
            set_status = "✗ SET"

        if reset_ok:
            reset_status = "✓ RESET"
        else:
            reset_status = "✗ RESET"

        if default_ok:
            default_status = "✓ DEFAULT"
        else:
            default_status = "✗ DEFAULT"

        print(
            f"{variavel:<18} "
            f"{set_status:<10} "
            f"{reset_status:<10} "
            f"{default_status}"
        )

    print()
    print("=" * 72)
    print("CONCLUSAO")
    print("=" * 72)
    print()

    total = len(resultados)

    sets_ok = sum(
        1
        for resultado in resultados
        if resultado.get("set_ok")
    )

    resets_ok = sum(
        1
        for resultado in resultados
        if resultado.get("reset_ok")
    )

    defaults_ok = sum(
        1
        for resultado in resultados
        if resultado.get("default_preservado")
    )

    print(
        f"Variáveis testadas : {total}"
    )

    print(
        f"SET confirmados    : {sets_ok}/{total}"
    )

    print(
        f"RESET confirmados  : {resets_ok}/{total}"
    )

    print(
        f"DEFAULT preservado : {defaults_ok}/{total}"
    )

    print()

    if (
        sets_ok == total
        and resets_ok == total
        and defaults_ok == total
    ):
        print(
            "✓ TODOS OS TESTES TEMPORÁRIOS "
            "PASSARAM."
        )
        print(
            "✓ Nenhum DEFAULT foi alterado."
        )
        print(
            "✓ Nenhum job foi enviado."
        )
        print(
            "✓ Nenhuma página foi impressa."
        )
    else:
        print(
            "⚠ Existem variáveis que precisam "
            "de investigação individual."
        )

    print()
    print(
        "Os resultados serão usados para "
        "construir a matriz real de comportamento "
        "da MX611."
    )
    print()


if __name__ == "__main__":
    main()