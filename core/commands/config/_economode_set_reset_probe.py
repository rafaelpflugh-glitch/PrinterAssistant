"""
PRINTER ASSISTANT
MX611 - ECONOMODE SET / RESET PROBE

Investiga o comportamento temporário de ECONOMODE
através de SET e RESET.

Este teste:

- consulta INQUIRE;
- consulta DINQUIRE;
- executa SET ECONOMODE=ON;
- consulta novamente;
- executa RESET;
- consulta novamente;
- verifica se o DEFAULT permaneceu intacto.

NÃO:

- executa DEFAULT;
- envia job;
- imprime;
- altera configuração persistente.
"""

import socket
import time


VARIABLE = "ECONOMODE"
TEST_VALUE = "ON"

RAW_PORT = 9100
TIMEOUT = 5.0
RETRIES = 3


def conectar(ip):
    """
    Abre conexão RAW com tentativas.
    """

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


def enviar(ip, comando):
    """
    Envia um comando PJL através de uma conexão RAW
    independente.

    Não espera resposta útil para SET/RESET.
    """

    sock = conectar(ip)

    try:

        texto = (
            "\x1b%-12345X"
            f"{comando}\r\n"
            "\x1b%-12345X"
        )

        dados = texto.encode(
            "ascii",
            errors="replace",
        )

        inicio = time.perf_counter()

        sock.sendall(dados)

        tempo = time.perf_counter() - inicio

        return tempo

    finally:

        try:
            sock.shutdown(
                socket.SHUT_RDWR
            )

        except Exception:
            pass

        sock.close()


def consultar(ip, comando):
    """
    Envia INQUIRE ou DINQUIRE e captura a resposta.
    """

    sock = conectar(ip)

    try:

        texto = (
            "\x1b%-12345X"
            f"@PJL {comando}\r\n"
            "\x1b%-12345X"
        )

        dados = texto.encode(
            "ascii",
            errors="replace",
        )

        inicio = time.perf_counter()

        sock.sendall(dados)

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

        tempo = (
            time.perf_counter()
            - inicio
        )

        texto_resposta = resposta.decode(
            "latin-1",
            errors="replace",
        )

        linhas = []

        for linha in texto_resposta.splitlines():

            linha = linha.strip()

            if not linha:
                continue

            if linha.upper().startswith("@PJL"):
                continue

            if linha.startswith("\x1b"):
                continue

            linhas.append(linha)

        if linhas:
            valor = linhas[-1]
        else:
            valor = None

        return valor, tempo

    finally:

        try:
            sock.shutdown(
                socket.SHUT_RDWR
            )

        except Exception:
            pass

        sock.close()


def inquire(ip):
    """
    Consulta ECONOMODE corrente.
    """

    return consultar(
        ip,
        f"INQUIRE {VARIABLE}",
    )


def dinquire(ip):
    """
    Consulta ECONOMODE default.
    """

    return consultar(
        ip,
        f"DINQUIRE {VARIABLE}",
    )


def setar(ip):
    """
    Executa:

        @PJL SET ECONOMODE=ON
    """

    return enviar(
        ip,
        f"@PJL SET {VARIABLE}={TEST_VALUE}",
    )


def resetar(ip):
    """
    Executa:

        @PJL RESET
    """

    return enviar(
        ip,
        "@PJL RESET",
    )


def mostrar_estado(ip, titulo):
    """
    Consulta e exibe CURRENT e DEFAULT.
    """

    print()
    print(titulo)
    print("-" * 72)

    corrente, tempo_inquire = inquire(ip)
    padrao, tempo_dinquire = dinquire(ip)

    print(
        f"INQUIRE  : {corrente}"
    )

    print(
        f"DINQUIRE : {padrao}"
    )

    print(
        f"Tempo INQUIRE  : "
        f"{tempo_inquire:.3f}s"
    )

    print(
        f"Tempo DINQUIRE : "
        f"{tempo_dinquire:.3f}s"
    )

    return corrente, padrao


def main():

    print()
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - "
        "MX611 ECONOMODE SET / RESET PROBE"
    )
    print("=" * 72)

    print()
    print("Variável:")
    print(f"  {VARIABLE}")

    print()
    print("Valor de teste:")
    print(f"  {TEST_VALUE}")

    print()
    print("Este teste:")
    print()
    print("- consulta o estado corrente;")
    print("- consulta o DEFAULT;")
    print("- executa SET ECONOMODE=ON;")
    print("- consulta novamente;")
    print("- executa RESET;")
    print("- consulta novamente;")
    print("- verifica se o DEFAULT permaneceu intacto;")
    print("- NÃO executa DEFAULT;")
    print("- NÃO envia job;")
    print("- NÃO imprime nenhuma página.")

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

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":

        print()
        print("Teste cancelado.")

        return

    # ========================================================
    # 1. ESTADO ORIGINAL
    # ========================================================

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    try:

        original_corrente, original_default = (
            mostrar_estado(
                ip,
                "Estado original",
            )
        )

    except Exception as exc:

        print()
        print("ERRO AO CONSULTAR ESTADO ORIGINAL.")
        print(
            f"Tipo: {type(exc).__name__}"
        )
        print(
            f"Mensagem: {exc}"
        )

        return

    if original_corrente is None:

        print()
        print(
            "⚠ INQUIRE ECONOMODE "
            "não retornou valor."
        )

        return

    if original_default is None:

        print()
        print(
            "⚠ DINQUIRE ECONOMODE "
            "não retornou valor."
        )

        return

    # ========================================================
    # 2. SET
    # ========================================================

    print()
    print("=" * 72)
    print("2. SET")
    print("=" * 72)

    print()
    print(
        f"Enviando:"
    )

    print(
        f"@PJL SET {VARIABLE}={TEST_VALUE}"
    )

    try:

        tempo_set = setar(ip)

        print()
        print(
            f"SET enviado em "
            f"{tempo_set:.3f}s"
        )

    except Exception as exc:

        print()
        print("✗ ERRO AO ENVIAR SET.")
        print(
            f"Tipo: {type(exc).__name__}"
        )
        print(
            f"Mensagem: {exc}"
        )

        return

    time.sleep(0.5)

    # ========================================================
    # 3. ESTADO APÓS SET
    # ========================================================

    print()
    print("=" * 72)
    print("3. ESTADO APÓS SET")
    print("=" * 72)

    try:

        apos_set_corrente, apos_set_default = (
            mostrar_estado(
                ip,
                "Estado após SET",
            )
        )

    except Exception as exc:

        print()
        print(
            "✗ ERRO AO CONSULTAR "
            "ESTADO APÓS SET."
        )

        print(
            f"Tipo: {type(exc).__name__}"
        )

        print(
            f"Mensagem: {exc}"
        )

        return

    set_confirmado = (
        str(apos_set_corrente).upper()
        == str(TEST_VALUE).upper()
    )

    default_preservado = (
        str(apos_set_default).upper()
        == str(original_default).upper()
    )

    print()

    if set_confirmado:

        print(
            "✓ SET ALTEROU O "
            "AMBIENTE CORRENTE."
        )

    else:

        print(
            "✗ SET NÃO FOI CONFIRMADO "
            "PELO INQUIRE."
        )

    if default_preservado:

        print(
            "✓ DEFAULT PERMANECEU "
            "INALTERADO."
        )

    else:

        print(
            "⚠ DEFAULT FOI ALTERADO."
        )

    # ========================================================
    # 4. RESET
    # ========================================================

    print()
    print("=" * 72)
    print("4. RESET")
    print("=" * 72)

    print()
    print("Enviando:")
    print("@PJL RESET")

    try:

        tempo_reset = resetar(ip)

        print()
        print(
            f"RESET enviado em "
            f"{tempo_reset:.3f}s"
        )

    except Exception as exc:

        print()
        print(
            "✗ ERRO AO ENVIAR RESET."
        )

        print(
            f"Tipo: {type(exc).__name__}"
        )

        print(
            f"Mensagem: {exc}"
        )

        return

    time.sleep(1.0)

    # ========================================================
    # 5. ESTADO APÓS RESET
    # ========================================================

    print()
    print("=" * 72)
    print("5. ESTADO APÓS RESET")
    print("=" * 72)

    try:

        apos_reset_corrente, apos_reset_default = (
            mostrar_estado(
                ip,
                "Estado após RESET",
            )
        )

    except Exception as exc:

        print()
        print(
            "✗ ERRO AO CONSULTAR "
            "ESTADO APÓS RESET."
        )

        print(
            f"Tipo: {type(exc).__name__}"
        )

        print(
            f"Mensagem: {exc}"
        )

        return

    reset_corrente_confirmado = (
        str(apos_reset_corrente).upper()
        == str(original_corrente).upper()
    )

    reset_default_confirmado = (
        str(apos_reset_default).upper()
        == str(original_default).upper()
    )

    # ========================================================
    # 6. RESULTADO
    # ========================================================

    print()
    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    print()

    print(
        f"Corrente original : "
        f"{original_corrente}"
    )

    print(
        f"Default original  : "
        f"{original_default}"
    )

    print()

    print(
        f"Após SET INQUIRE  : "
        f"{apos_set_corrente}"
    )

    print(
        f"Após SET DINQUIRE : "
        f"{apos_set_default}"
    )

    print()

    print(
        f"Após RESET INQUIRE  : "
        f"{apos_reset_corrente}"
    )

    print(
        f"Após RESET DINQUIRE : "
        f"{apos_reset_default}"
    )

    print()

    print("-" * 72)

    if set_confirmado:

        print(
            "✓ SET: CONFIRMADO "
            "NO AMBIENTE CORRENTE."
        )

    else:

        print(
            "✗ SET: NÃO CONFIRMADO "
            "POR INQUIRE."
        )

    if default_preservado:

        print(
            "✓ DEFAULT: PRESERVADO."
        )

    else:

        print(
            "⚠ DEFAULT: ALTERADO."
        )

    if reset_corrente_confirmado:

        print(
            "✓ RESET: RESTAUROU "
            "O AMBIENTE CORRENTE."
        )

    else:

        print(
            "⚠ RESET: NÃO RESTAUROU "
            "EXATAMENTE O ESTADO ORIGINAL."
        )

    if reset_default_confirmado:

        print(
            "✓ RESET: DEFAULT "
            "PERMANECEU ORIGINAL."
        )

    else:

        print(
            "⚠ RESET: DEFAULT "
            "NÃO ESTÁ ORIGINAL."
        )

    print()
    print("-" * 72)

    print(
        "INTERPRETAÇÃO:"
    )

    print()

    if (
        set_confirmado
        and default_preservado
        and reset_corrente_confirmado
        and reset_default_confirmado
    ):

        print(
            "✓ ECONOMODE demonstrou "
            "SET/RESET confirmado."
        )

        print(
            "✓ O SET alterou apenas "
            "o ambiente corrente."
        )

        print(
            "✓ O DEFAULT permaneceu intacto."
        )

        print(
            "✓ RESET restaurou o ambiente."
        )

        print()
        print(
            "Próxima etapa futura:"
        )

        print(
            "investigar se ECONOMODE "
            "produz efeito físico "
            "observável em um job."
        )

    else:

        print(
            "ECONOMODE ainda NÃO deve "
            "ser promovido no Capability Model."
        )

        print(
            "O resultado precisa ser "
            "investigado antes de qualquer "
            "integração."
        )

    print()
    print("=" * 72)
    print("FIM DO PROBE")
    print("=" * 72)


if __name__ == "__main__":
    main()