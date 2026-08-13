"""
Printer Assistant - PJL Reset Probe

Investiga se @PJL RESET faz a configuração corrente
voltar aos valores DEFAULT.

Este teste utiliza somente DENSITY.
"""

import socket
import time

from core.commands.config_writer import PJLWriter


VARIAVEL = "DENSITY"
VALOR_TESTE = "4"
VALOR_ORIGINAL = "3"


def estado(writer):
    return {
        "inquire": writer.inquire(VARIAVEL),
        "dinquire": writer.dinquire(VARIAVEL),
    }


def enviar_reset(ip, port=9100, timeout=5):
    writer = PJLWriter(
        ip=ip,
        port=port,
        timeout=timeout,
    )

    try:
        writer.conectar()

        print()
        print("Enviando:")
        print("@PJL RESET")

        resposta = writer.enviar(
            "@PJL RESET",
            espera=0.5,
        )

        if resposta:
            print()
            print("Resposta:")
            print(resposta)
        else:
            print()
            print("(sem resposta PJL)")

    finally:
        writer.fechar()


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL RESET PROBE")
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

    print("Variável controlada:")
    print(f"  {VARIAVEL}")
    print()

    print("Sequência:")
    print("  1. Ler estado original")
    print("  2. DEFAULT DENSITY=4")
    print("  3. Confirmar corrente/default")
    print("  4. DEFAULT DENSITY=3")
    print("  5. Confirmar que corrente continua em 4")
    print("  6. Enviar @PJL RESET")
    print("  7. Verificar INQUIRE/DINQUIRE")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    writer = PJLWriter(
        ip=ip,
        port=9100,
        timeout=5,
    )

    try:
        writer.conectar()

        print()
        print("=" * 72)
        print("1. ESTADO ORIGINAL")
        print("=" * 72)

        original = estado(writer)

        print(
            f"INQUIRE  : {original['inquire']}"
        )

        print(
            f"DINQUIRE : {original['dinquire']}"
        )

        if (
            str(original["inquire"]).upper()
            != VALOR_ORIGINAL
            or
            str(original["dinquire"]).upper()
            != VALOR_ORIGINAL
        ):
            print()
            print(
                "⚠ O estado original não corresponde "
                f"ao esperado ({VALOR_ORIGINAL})."
            )

            print(
                "Teste interrompido para evitar "
                "alteração inesperada."
            )

            return

        print()
        print("=" * 72)
        print("2. ALTERANDO DEFAULT")
        print("=" * 72)

        print()
        print(
            f"@PJL DEFAULT {VARIAVEL}={VALOR_TESTE}"
        )

        writer.default(
            VARIAVEL,
            VALOR_TESTE,
        )

        time.sleep(0.5)

        depois_default = estado(writer)

        print()
        print(
            f"INQUIRE  : "
            f"{depois_default['inquire']}"
        )

        print(
            f"DINQUIRE : "
            f"{depois_default['dinquire']}"
        )

        print()
        print("=" * 72)
        print("3. RESTAURANDO DEFAULT")
        print("=" * 72)

        print()
        print(
            f"@PJL DEFAULT {VARIAVEL}="
            f"{VALOR_ORIGINAL}"
        )

        writer.default(
            VARIAVEL,
            VALOR_ORIGINAL,
        )

        time.sleep(0.5)

        depois_restauracao = estado(writer)

        print()
        print(
            f"INQUIRE  : "
            f"{depois_restauracao['inquire']}"
        )

        print(
            f"DINQUIRE : "
            f"{depois_restauracao['dinquire']}"
        )

        print()
        print("=" * 72)
        print("4. TESTANDO RESET")
        print("=" * 72)

        writer.fechar()

        enviar_reset(
            ip=ip,
            port=9100,
            timeout=5,
        )

        time.sleep(1.0)

        writer.conectar()

        depois_reset = estado(writer)

        print()
        print("Estado depois de @PJL RESET:")
        print()
        print(
            f"INQUIRE  : "
            f"{depois_reset['inquire']}"
        )

        print(
            f"DINQUIRE : "
            f"{depois_reset['dinquire']}"
        )

        print()
        print("=" * 72)
        print("RESULTADO")
        print("=" * 72)

        corrente_original = str(
            original["inquire"]
        ).upper()

        corrente_final = str(
            depois_reset["inquire"]
        ).upper()

        default_final = str(
            depois_reset["dinquire"]
        ).upper()

        print()
        print(
            f"Corrente original : "
            f"{corrente_original}"
        )

        print(
            f"Corrente final    : "
            f"{corrente_final}"
        )

        print(
            f"Default final     : "
            f"{default_final}"
        )

        print()

        if corrente_final == VALOR_ORIGINAL:
            print(
                "✓ RESET FEZ A CONFIGURAÇÃO "
                "CORRENTE VOLTAR AO DEFAULT."
            )
        else:
            print(
                "⚠ RESET NÃO RESTAURou "
                "A CONFIGURAÇÃO CORRENTE."
            )

        if default_final == VALOR_ORIGINAL:
            print(
                "✓ DEFAULT PERMANECE RESTAURADO."
            )
        else:
            print(
                "⚠ DEFAULT NÃO ESTÁ NO VALOR ORIGINAL."
            )

    except Exception as exc:
        print()
        print("=" * 72)
        print("ERRO")
        print("=" * 72)
        print(
            f"Tipo: {type(exc).__name__}"
        )
        print(
            f"Mensagem: {exc}"
        )

    finally:
        try:
            writer.fechar()
        except Exception:
            pass

        print()
        print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()