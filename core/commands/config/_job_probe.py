"""
Printer Assistant - PJL Job Behavior Probe

Teste funcional controlado de configurações PJL.

O teste:
1. Descobre os valores atuais.
2. Altera DEFAULTs selecionados.
3. Confirma INQUIRE e DINQUIRE.
4. Envia um pequeno job PCL.
5. Restaura os valores originais.
6. Confirma a restauração.

ATENÇÃO:
Este teste imprime uma página física.
"""

import socket
import time

from core.commands.config_writer import PJLWriter


TEST_PROFILE = {
    "DUPLEX": "ON",
    "RESOLUTION": "1200",
    "ORIENTATION": "LANDSCAPE",
    "DENSITY": "4",
}


def descobrir_estado(writer, variavel):
    corrente = writer.inquire(variavel)
    padrao = writer.dinquire(variavel)

    return {
        "corrente": corrente,
        "default": padrao,
    }


def enviar_job_pcl(ip, port=9100, timeout=5):
    """
    Envia um job PCL mínimo de uma página.
    """

    job = (
        "\x1b%-12345X"
        "@PJL JOB NAME=\"PRINTER_ASSISTANT_PROBE\"\r\n"
        "@PJL ENTER LANGUAGE=PCL\r\n"
        "\x1b&l1O"
        "\x1b&l0E"
        "\x1b&a0L"
        "\x1b&a0M"
        "\x1b*p100x100Y"
        "\x1b(s1p10v0s0b4101T"
        "PRINTER ASSISTANT TEST"
        "\x0c"
        "\x1b%-12345X"
    )

    print()
    print("Abrindo conexão RAW para o job...")
    print(f"Conectando em {ip}:{port}")

    sock = socket.create_connection(
        (ip, port),
        timeout=timeout,
    )

    try:
        sock.settimeout(timeout)

        dados = job.encode(
            "latin-1",
            errors="replace",
        )

        inicio = time.monotonic()

        sock.sendall(dados)

        tempo = time.monotonic() - inicio

        print("Job enviado.")
        print(f"Bytes enviados: {len(dados)}")
        print(f"Tempo de envio: {tempo:.3f}s")

        time.sleep(0.5)

    finally:
        sock.close()

    print("Conexão do job encerrada.")


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL JOB BEHAVIOR PROBE")
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

    print("Este teste irá:")
    print()
    print("1. Descobrir os valores atuais.")
    print("2. Alterar temporariamente os DEFAULTs:")
    print()

    for variavel, valor in TEST_PROFILE.items():
        print(f"   {variavel:<15} -> {valor}")

    print()
    print("3. Enviar UMA página de teste.")
    print("4. Restaurar automaticamente os valores originais.")
    print()

    confirmar = input(
        "ATENÇÃO: a impressora irá imprimir. Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    writer = PJLWriter(
        ip=ip,
        port=9100,
        timeout=5,
    )

    originais = {}

    try:
        print()
        print("=" * 72)
        print("1. ESTADO ORIGINAL")
        print("=" * 72)

        writer.conectar()

        for variavel in TEST_PROFILE:
            estado = descobrir_estado(
                writer,
                variavel,
            )

            originais[variavel] = estado

            print()
            print(variavel)
            print(f"  INQUIRE  : {estado['corrente']}")
            print(f"  DINQUIRE : {estado['default']}")

        print()
        print("=" * 72)
        print("2. APLICANDO DEFAULTs DE TESTE")
        print("=" * 72)

        for variavel, valor in TEST_PROFILE.items():
            print()
            print(
                f"Enviando: "
                f"@PJL DEFAULT {variavel}={valor}"
            )

            writer.default(
                variavel,
                valor,
            )

            time.sleep(0.3)

            estado = descobrir_estado(
                writer,
                variavel,
            )

            print(
                f"INQUIRE  : {estado['corrente']}"
            )

            print(
                f"DINQUIRE : {estado['default']}"
            )

        print()
        print("=" * 72)
        print("3. VERIFICAÇÃO DOS DEFAULTs")
        print("=" * 72)

        perfil_ok = True

        for variavel, valor in TEST_PROFILE.items():
            estado = descobrir_estado(
                writer,
                variavel,
            )

            corrente_ok = (
                str(estado["corrente"]).upper()
                == str(valor).upper()
            )

            default_ok = (
                str(estado["default"]).upper()
                == str(valor).upper()
            )

            print()
            print(variavel)
            print(f"  Esperado : {valor}")
            print(f"  INQUIRE  : {estado['corrente']}")
            print(f"  DINQUIRE : {estado['default']}")

            if corrente_ok and default_ok:
                print("  ✓ CONFIRMADO")
            else:
                print("  ✗ NÃO CONFIRMADO")
                perfil_ok = False

        print()
        print("=" * 72)
        print("4. ENVIO DO JOB")
        print("=" * 72)

        print()
        print("Será enviada uma página PCL.")
        print()
        print("Observe fisicamente:")
        print("  - orientação")
        print("  - duplex")
        print("  - qualidade/densidade")
        print("  - comportamento geral do job")
        print()

        input(
            "Pressione ENTER para enviar o job..."
        )

        writer.fechar()

        enviar_job_pcl(
            ip=ip,
            port=9100,
            timeout=5,
        )

        print()
        print("=" * 72)
        print("5. RESTAURAÇÃO")
        print("=" * 72)

        writer.conectar()

        for variavel, estado_original in originais.items():
            valor_original = estado_original["default"]

            print()
            print(
                f"Restaurando: "
                f"@PJL DEFAULT "
                f"{variavel}={valor_original}"
            )

            writer.default(
                variavel,
                valor_original,
            )

            time.sleep(0.3)

            estado_final = descobrir_estado(
                writer,
                variavel,
            )

            print(
                f"INQUIRE  : "
                f"{estado_final['corrente']}"
            )

            print(
                f"DINQUIRE : "
                f"{estado_final['default']}"
            )

        print()
        print("=" * 72)
        print("6. VERIFICAÇÃO FINAL")
        print("=" * 72)

        restauracao_ok = True

        for variavel, estado_original in originais.items():
            estado_final = descobrir_estado(
                writer,
                variavel,
            )

            corrente_ok = (
                str(estado_final["corrente"]).upper()
                == str(estado_original["corrente"]).upper()
            )

            default_ok = (
                str(estado_final["default"]).upper()
                == str(estado_original["default"]).upper()
            )

            print()
            print(variavel)

            print(
                f"  Corrente original : "
                f"{estado_original['corrente']}"
            )

            print(
                f"  Corrente final    : "
                f"{estado_final['corrente']}"
            )

            print(
                f"  Default original  : "
                f"{estado_original['default']}"
            )

            print(
                f"  Default final     : "
                f"{estado_final['default']}"
            )

            if corrente_ok and default_ok:
                print("  ✓ RESTAURADO")
            else:
                print("  ✗ RESTAURAÇÃO DIFERENTE")
                restauracao_ok = False

        print()
        print("=" * 72)
        print("RESULTADO")
        print("=" * 72)

        if perfil_ok:
            print("✓ DEFAULTs DE TESTE CONFIRMADOS.")
        else:
            print("⚠ ALGUM DEFAULT NÃO FOI CONFIRMADO.")

        if restauracao_ok:
            print("✓ CONFIGURAÇÕES RESTAURADAS.")
        else:
            print("⚠ VERIFIQUE A CONFIGURAÇÃO FINAL.")

        print()
        print(
            "A aparência física da página deve ser "
            "analisada manualmente."
        )

    except Exception as exc:
        print()
        print("=" * 72)
        print("ERRO DURANTE O TESTE")
        print("=" * 72)
        print(f"Tipo: {type(exc).__name__}")
        print(f"Mensagem: {exc}")

    finally:
        try:
            writer.fechar()
        except Exception:
            pass

        print()
        print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()