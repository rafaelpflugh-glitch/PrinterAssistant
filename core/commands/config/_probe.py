"""
Printer Assistant - Probe de configuração PJL

Teste controlado do motor genérico de configuração.

Fluxo:

    DINQUIRE LANG
    INQUIRE LANG

    DEFAULT LANG=ENGLISH

    INQUIRE LANG
    DINQUIRE LANG

    DEFAULT LANG=PORTUGUESE

    INQUIRE LANG
    DINQUIRE LANG
"""

from ._manager import PJLConfigManager


def linha():
    print("=" * 72)


def main():
    linha()
    print("PRINTER ASSISTANT - PJL CONFIG PROBE")
    linha()

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(f"Impressora: {ip}")
    print("RAW:        " + ip + ":9100")
    print()
    print("Teste controlado:")
    print("  Variável: LANG")
    print("  Teste:    ENGLISH")
    print("  Original: descoberta automaticamente")
    print("  Final:    restauração automática")
    print()

    confirmar = input("Continuar? [S/N]: ").strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    manager = PJLConfigManager(
        ip=ip,
        porta=9100,
        timeout=4.0,
    )

    try:
        print()
        print("Abrindo conexão RAW...")
        manager.conectar()

        print("Conectado.")
        print()

        linha()
        print("1. ESTADO INICIAL")
        linha()

        print()
        print("DINQUIRE LANG")
        print()

        default_original = manager.dinquire("LANG")

        print(
            f"DEFAULT ORIGINAL: {default_original}"
        )

        print()
        print("INQUIRE LANG")
        print()

        corrente_original = manager.inquire("LANG")

        print(
            f"VALOR CORRENTE ORIGINAL: "
            f"{corrente_original}"
        )

        if default_original is None:
            print()
            print(
                "✗ Não foi possível descobrir "
                "o DEFAULT de LANG."
            )
            return

        if corrente_original is None:
            print()
            print(
                "✗ Não foi possível descobrir "
                "o valor corrente de LANG."
            )
            return

        print()
        linha()
        print("2. ALTERAÇÃO PERSISTENTE")
        linha()

        print()
        print("Enviando:")
        print("@PJL DEFAULT LANG=ENGLISH")
        print()

        manager.default(
            "LANG",
            "ENGLISH",
        )

        print("(sem resposta PJL esperada)")
        print()

        print("INQUIRE LANG após DEFAULT:")
        corrente_depois = manager.inquire(
            "LANG"
        )

        print(
            f"VALOR CORRENTE: {corrente_depois}"
        )

        print()
        print("DINQUIRE LANG após DEFAULT:")
        default_depois = manager.dinquire(
            "LANG"
        )

        print(
            f"VALOR DEFAULT: {default_depois}"
        )

        print()
        linha()
        print("3. VERIFICAÇÃO")
        linha()

        sucesso_default = (
            str(default_depois).strip().upper()
            == "ENGLISH"
        )

        sucesso_corrente = (
            str(corrente_depois).strip().upper()
            == "ENGLISH"
        )

        if sucesso_default:
            print(
                "✓ DINQUIRE confirma "
                "DEFAULT LANG=ENGLISH"
            )
        else:
            print(
                "✗ DINQUIRE NÃO confirmou "
                "LANG=ENGLISH"
            )

        if sucesso_corrente:
            print(
                "✓ INQUIRE confirma "
                "LANG=ENGLISH"
            )
        else:
            print(
                "✗ INQUIRE NÃO confirmou "
                "LANG=ENGLISH"
            )

        print()
        linha()
        print("4. RESTAURAÇÃO")
        linha()

        print()
        print(
            f"Restaurando DEFAULT LANG="
            f"{default_original}"
        )

        manager.default(
            "LANG",
            default_original,
        )

        print()
        print("INQUIRE LANG final:")

        corrente_final = manager.inquire(
            "LANG"
        )

        print(
            f"VALOR CORRENTE FINAL: "
            f"{corrente_final}"
        )

        print()
        print("DINQUIRE LANG final:")

        default_final = manager.dinquire(
            "LANG"
        )

        print(
            f"VALOR DEFAULT FINAL: "
            f"{default_final}"
        )

        print()
        linha()
        print("5. RESULTADO FINAL")
        linha()

        restaurado = (
            str(default_final).strip().upper()
            == str(default_original).strip().upper()
        )

        if restaurado:
            print(
                "✓ DEFAULT LANG RESTAURADO."
            )
        else:
            print(
                "✗ DEFAULT LANG NÃO FOI "
                "RESTAURADO CORRETAMENTE."
            )

        print()

        print(
            f"Inicial DEFAULT : "
            f"{default_original}"
        )

        print(
            f"Inicial corrente: "
            f"{corrente_original}"
        )

        print(
            f"Após DEFAULT    : "
            f"{default_depois}"
        )

        print(
            f"Após DEFAULT INQ: "
            f"{corrente_depois}"
        )

        print(
            f"Final DEFAULT   : "
            f"{default_final}"
        )

        print(
            f"Final corrente  : "
            f"{corrente_final}"
        )

        print()
        linha()

    except Exception as exc:
        print()
        print("✗ ERRO DURANTE O TESTE")
        print()
        print(type(exc).__name__)
        print(str(exc))

    finally:
        try:
            manager.fechar()
        except Exception:
            pass

        print()
        print("Conexão RAW encerrada.")
        linha()


if __name__ == "__main__":
    main()
