"""
Printer Assistant - PJL Job Reset Probe

Investiga a relação entre:

DEFAULT
job
RESET
INQUIRE
DINQUIRE

O teste usa ORIENTATION porque já foi confirmado
experimentalmente que DEFAULT ORIENTATION influencia
o comportamento físico do job.

Todas as alterações de DEFAULT são restauradas.
"""

import socket
import time


VARIABLE = "ORIENTATION"
TEST_VALUE = "LANDSCAPE"


def enviar_pjl(ip, comando, timeout=5):
    if not comando.endswith("\r\n"):
        comando += "\r\n"

    resposta = bytearray()

    with socket.create_connection(
        (ip, 9100),
        timeout=timeout,
    ) as sock:

        sock.settimeout(timeout)

        sock.sendall(
            comando.encode(
                "ascii",
                errors="replace",
            )
        )

        time.sleep(0.15)

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


def extrair_valor(resposta, variavel):
    if not resposta:
        return None

    alvo = variavel.upper()

    for linha in resposta.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        if linha.upper().startswith("@PJL"):
            continue

        if "=" in linha:
            nome, valor = linha.split("=", 1)

            if nome.strip().upper() == alvo:
                return valor.strip().strip('"')

        return linha.strip('"')

    return None


def inquire(ip, variavel):
    resposta = enviar_pjl(
        ip,
        f"@PJL INQUIRE {variavel}",
    )

    return extrair_valor(
        resposta,
        variavel,
    )


def dinquire(ip, variavel):
    resposta = enviar_pjl(
        ip,
        f"@PJL DINQUIRE {variavel}",
    )

    return extrair_valor(
        resposta,
        variavel,
    )


def default(ip, variavel, valor):
    enviar_pjl(
        ip,
        f"@PJL DEFAULT {variavel}={valor}",
    )


def reset(ip):
    enviar_pjl(
        ip,
        "@PJL RESET",
    )


def criar_job():
    partes = [
        b"\x1b%-12345X",
        b"@PJL JOB NAME=\"PA_RESET_PROBE\"\r\n",
        b"@PJL ENTER LANGUAGE=PCL\r\n",
        b"\x1bE",
        b"PRINTER ASSISTANT\r\n",
        b"PJL RESET BEHAVIOR PROBE\r\n",
        b"\x0c",
        b"\x1b%-12345X",
    ]

    return b"".join(partes)


def enviar_job(ip):
    dados = criar_job()

    inicio = time.monotonic()

    with socket.create_connection(
        (ip, 9100),
        timeout=5,
    ) as sock:

        sock.sendall(dados)

    return (
        len(dados),
        time.monotonic() - inicio,
    )


def mostrar_estado(ip, titulo):
    corrente = inquire(
        ip,
        VARIABLE,
    )

    padrao = dinquire(
        ip,
        VARIABLE,
    )

    print()
    print("=" * 72)
    print(titulo)
    print("=" * 72)
    print(
        f"INQUIRE  : {corrente}"
    )
    print(
        f"DINQUIRE : {padrao}"
    )

    return corrente, padrao


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL JOB RESET PROBE")
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(
        f"Impressora: {ip}"
    )
    print(
        "RAW:        9100"
    )

    print()
    print(
        "Variável controlada:"
    )
    print(
        f"{VARIABLE}"
    )

    print()
    print(
        "Sequência:"
    )
    print(
        "1. Ler estado original"
    )
    print(
        "2. DEFAULT ORIENTATION=LANDSCAPE"
    )
    print(
        "3. Enviar um job"
    )
    print(
        "4. DEFAULT ORIENTATION=PORTRAIT"
    )
    print(
        "5. Verificar ambiente corrente"
    )
    print(
        "6. RESET"
    )
    print(
        "7. Verificar novamente"
    )

    print()

    confirmar = input(
        "A impressora irá imprimir. "
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print(
            "Teste cancelado."
        )
        return

    original_current = None
    original_default = None

    try:
        original_current, original_default = (
            mostrar_estado(
                ip,
                "1. ESTADO ORIGINAL",
            )
        )

        if (
            original_current is None
            or original_default is None
        ):
            raise RuntimeError(
                "Não foi possível descobrir "
                "o estado original."
            )

        print()
        print("=" * 72)
        print("2. DEFAULT LANDSCAPE")
        print("=" * 72)

        print(
            f"@PJL DEFAULT "
            f"{VARIABLE}={TEST_VALUE}"
        )

        default(
            ip,
            VARIABLE,
            TEST_VALUE,
        )

        mostrar_estado(
            ip,
            "ESTADO APÓS DEFAULT LANDSCAPE",
        )

        print()
        print("=" * 72)
        print("3. ENVIO DO JOB")
        print("=" * 72)

        print()
        print(
            "O job não contém "
            "ORIENTATION."
        )

        print(
            "A impressora deverá utilizar "
            "o DEFAULT LANDSCAPE."
        )

        input(
            "Pressione ENTER para enviar "
            "o job..."
        )

        bytes_enviados, tempo = enviar_job(
            ip
        )

        print()
        print(
            "Job enviado."
        )

        print(
            f"Bytes enviados: "
            f"{bytes_enviados}"
        )

        print(
            f"Tempo: "
            f"{tempo:.3f}s"
        )

        print()
        print(
            "Verifique fisicamente "
            "a orientação da página."
        )

        print()
        print("=" * 72)
        print("4. RESTAURANDO DEFAULT PORTRAIT")
        print("=" * 72)

        print(
            "@PJL DEFAULT "
            "ORIENTATION=PORTRAIT"
        )

        default(
            ip,
            VARIABLE,
            original_default,
        )

        corrente_apos_restore, default_apos_restore = (
            mostrar_estado(
                ip,
                "ESTADO APÓS RESTAURAÇÃO DO DEFAULT",
            )
        )

        print()
        print(
            "Esperado neste ponto:"
        )

        print(
            "  corrente = LANDSCAPE"
        )

        print(
            "  default   = PORTRAIT"
        )

        print()
        print("=" * 72)
        print("5. RESET")
        print("=" * 72)

        print(
            "Enviando:"
        )

        print(
            "@PJL RESET"
        )

        reset(ip)

        corrente_final, default_final = (
            mostrar_estado(
                ip,
                "ESTADO APÓS RESET",
            )
        )

        print()
        print("=" * 72)
        print("6. RESULTADO")
        print("=" * 72)

        print()
        print(
            f"Corrente original : "
            f"{original_current}"
        )

        print(
            f"Default original  : "
            f"{original_default}"
        )

        print(
            f"Após DEFAULT TESTE:"
        )

        print(
            f"  corrente : "
            f"{inquire(ip, VARIABLE)}"
        )

        print(
            f"  default  : "
            f"{dinquire(ip, VARIABLE)}"
        )

        print()
        print(
            f"Após restauração:"
        )

        print(
            f"  corrente : "
            f"{corrente_apos_restore}"
        )

        print(
            f"  default  : "
            f"{default_apos_restore}"
        )

        print()
        print(
            f"Após RESET:"
        )

        print(
            f"  corrente : "
            f"{corrente_final}"
        )

        print(
            f"  default  : "
            f"{default_final}"
        )

        print()

        if (
            str(default_final).upper()
            == str(original_default).upper()
            and
            str(corrente_final).upper()
            == str(original_default).upper()
        ):
            print(
                "✓ RESET SINCRONIZOU O AMBIENTE "
                "COM O DEFAULT."
            )
        else:
            print(
                "✗ RESET NÃO SINCRONIZOU "
                "O AMBIENTE COM O DEFAULT."
            )

    finally:
        if original_default is not None:
            print()
            print("=" * 72)
            print(
                "RESTAURAÇÃO DE SEGURANÇA"
            )
            print("=" * 72)

            default(
                ip,
                VARIABLE,
                original_default,
            )

            reset(
                ip
            )

            corrente_segura = inquire(
                ip,
                VARIABLE,
            )

            default_seguro = dinquire(
                ip,
                VARIABLE,
            )

            print(
                f"INQUIRE  : "
                f"{corrente_segura}"
            )

            print(
                f"DINQUIRE : "
                f"{default_seguro}"
            )

    print()
    print(
        "Conexão RAW encerrada."
    )


if __name__ == "__main__":
    main()