"""
Printer Assistant - PJL SET / RESET Probe

Investiga o comportamento de uma configuração temporária
através de SET e RESET.

Este teste não altera o DEFAULT da impressora.
"""

import time

from core.commands.config_writer import PJLWriter


VARIABLE = "DENSITY"
TEST_VALUE = "4"


def ler_estado(writer):
    return {
        "corrente": writer.inquire(VARIABLE),
        "default": writer.dinquire(VARIABLE),
    }


def imprimir_estado(titulo, estado):
    print()
    print(titulo)
    print("-" * 72)
    print(f"INQUIRE  : {estado['corrente']}")
    print(f"DINQUIRE : {estado['default']}")


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL SET / RESET PROBE")
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
    print(f"  {VARIABLE}")
    print()
    print("Valor de teste:")
    print(f"  {TEST_VALUE}")
    print()
    print("Este teste:")
    print("  - NÃO altera o DEFAULT.")
    print("  - testa SET.")
    print("  - testa RESET.")
    print("  - verifica INQUIRE.")
    print("  - verifica DINQUIRE.")
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

        # ------------------------------------------------------
        # 1. ESTADO ORIGINAL
        # ------------------------------------------------------

        print()
        print("=" * 72)
        print("1. ESTADO ORIGINAL")
        print("=" * 72)

        original = ler_estado(writer)

        imprimir_estado(
            "Estado original",
            original,
        )

        original_corrente = original["corrente"]
        original_default = original["default"]

        if original_corrente is None:
            print()
            print("⚠ Não foi possível descobrir INQUIRE.")
            return

        if original_default is None:
            print()
            print("⚠ Não foi possível descobrir DINQUIRE.")
            return

        # ------------------------------------------------------
        # 2. SET
        # ------------------------------------------------------

        print()
        print("=" * 72)
        print("2. SET")
        print("=" * 72)

        print()
        print(
            f"Enviando: @PJL SET "
            f"{VARIABLE}={TEST_VALUE}"
        )

        resposta = writer.set(
            VARIABLE,
            TEST_VALUE,
        )

        if resposta:
            print()
            print("Resposta:")
            print(resposta)
        else:
            print()
            print("(sem resposta PJL)")

        time.sleep(0.5)

        depois_set = ler_estado(writer)

        imprimir_estado(
            "Estado após SET",
            depois_set,
        )

        # ------------------------------------------------------
        # 3. RESET
        # ------------------------------------------------------

        print()
        print("=" * 72)
        print("3. RESET")
        print("=" * 72)

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

        time.sleep(1.0)

        depois_reset = ler_estado(writer)

        imprimir_estado(
            "Estado após RESET",
            depois_reset,
        )

        # ------------------------------------------------------
        # 4. RESULTADO
        # ------------------------------------------------------

        print()
        print("=" * 72)
        print("RESULTADO")
        print("=" * 72)

        print()
        print(f"Corrente original : {original_corrente}")
        print(f"Default original  : {original_default}")
        print()
        print(f"Após SET INQUIRE  : {depois_set['corrente']}")
        print(f"Após SET DINQUIRE : {depois_set['default']}")
        print()
        print(
            f"Após RESET INQUIRE  : "
            f"{depois_reset['corrente']}"
        )
        print(
            f"Após RESET DINQUIRE : "
            f"{depois_reset['default']}"
        )

        print()

        corrente_set_aplicado = (
            str(depois_set["corrente"]).upper()
            == str(TEST_VALUE).upper()
        )

        default_nao_alterado = (
            str(depois_set["default"]).upper()
            == str(original_default).upper()
        )

        corrente_reset = (
            str(depois_reset["corrente"]).upper()
            == str(original_corrente).upper()
        )

        default_reset = (
            str(depois_reset["default"]).upper()
            == str(original_default).upper()
        )

        if corrente_set_aplicado:
            print("✓ SET ALTEROU O AMBIENTE CORRENTE.")
        else:
            print("✗ SET NÃO ALTEROU O AMBIENTE CORRENTE.")

        if default_nao_alterado:
            print("✓ SET NÃO ALTEROU O DEFAULT.")
        else:
            print("⚠ SET ALTEROU O DEFAULT.")

        if corrente_reset:
            print(
                "✓ RESET RESTAUROU O AMBIENTE "
                "CORRENTE."
            )
        else:
            print(
                "⚠ RESET NÃO RESTAUROU O AMBIENTE "
                "CORRENTE."
            )

        if default_reset:
            print(
                "✓ DEFAULT PERMANECEU NO VALOR ORIGINAL."
            )
        else:
            print(
                "⚠ DEFAULT NÃO ESTÁ NO VALOR ORIGINAL."
            )

        print()
        print(
            "Nenhum DEFAULT foi alterado durante "
            "este teste."
        )

    except Exception as exc:
        print()
        print("=" * 72)
        print("ERRO")
        print("=" * 72)
        print(f"Tipo: {type(exc).__name__}")
        print(f"Mensagem: {exc}")

    finally:
        writer.fechar()

        print()
        print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()