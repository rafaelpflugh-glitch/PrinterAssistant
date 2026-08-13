"""
Printer Assistant - Configuration Engine Probe

Primeiro teste real do motor genérico.

Teste:

    LANG = PORTUGUESE
        ↓
    DEFAULT LANG=ENGLISH
        ↓
    verificar
        ↓
    DEFAULT LANG=PORTUGUESE
        ↓
    verificar

Não altera outras configurações.
"""

from .config._manager import ConfigManager


def linha():
    print("-" * 72)


def main():

    print()
    print("=" * 72)
    print("PRINTER ASSISTANT - CONFIGURATION ENGINE PROBE")
    print("=" * 72)
    print()

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
        return

    manager = ConfigManager(ip)

    try:

        print()
        print("Conectando...")
        print()

        variaveis = manager.descobrir()

        if not variaveis:
            print("Nenhuma variável foi descoberta.")
            return

        print(
            f"Variáveis descobertas: {len(variaveis)}"
        )

        linha()

        # ==================================================
        # LANG
        # ==================================================

        lang = manager.obter("LANG")

        if lang is None:
            print("A impressora não declarou LANG.")
            return

        print()
        print("VARIÁVEL: LANG")
        print()

        print(
            f"Tipo:     {lang.get('tipo')}"
        )

        print(
            f"Atual:    {lang.get('valor')}"
        )

        print(
            f"Readonly: {lang.get('readonly')}"
        )

        print()
        print("Valores declarados pela impressora:")

        for valor in lang.get("valores", []):
            print(
                f"  - {valor}"
            )

        linha()

        # ==================================================
        # TESTE
        # ==================================================

        original = manager.padrao("LANG")

        if original is None:
            original = lang.get("valor")

        print()
        print(
            f"DEFAULT original: {original}"
        )

        print()
        print(
            "O próximo passo alterará temporariamente "
            "o idioma para ENGLISH."
        )

        confirma = input(
            "Continuar? [S/N]: "
        ).strip().upper()

        if confirma != "S":
            print("Teste cancelado.")
            return

        # ==================================================
        # ENGLISH
        # ==================================================

        print()
        print("=" * 72)
        print("ALTERANDO PARA ENGLISH")
        print("=" * 72)
        print()

        resultado = manager.alterar_default(
            "LANG",
            "ENGLISH",
        )

        print()
        print(
            "Resultado:"
        )

        print(
            f"Sucesso: {resultado['sucesso']}"
        )

        print(
            resultado["mensagem"]
        )

        verificacao = resultado.get(
            "verificacao"
        )

        if verificacao:

            print()
            print(
                f"INQUIRE : {verificacao['corrente']}"
            )

            print(
                f"DINQUIRE: {verificacao['default']}"
            )

        # ==================================================
        # RESTAURAÇÃO
        # ==================================================

        print()
        print("=" * 72)
        print("RESTAURANDO IDIOMA ORIGINAL")
        print("=" * 72)
        print()

        print(
            f"Restaurando LANG={original}"
        )

        restauracao = manager.restaurar_default(
            "LANG",
            original,
        )

        print()
        print(
            f"Sucesso: {restauracao['sucesso']}"
        )

        print(
            restauracao["mensagem"]
        )

        verificacao_final = restauracao.get(
            "verificacao"
        )

        if verificacao_final:

            print()
            print(
                f"INQUIRE final : "
                f"{verificacao_final['corrente']}"
            )

            print(
                f"DINQUIRE final: "
                f"{verificacao_final['default']}"
            )

        print()
        print("=" * 72)
        print("FIM DO TESTE")
        print("=" * 72)

    finally:

        manager.fechar()


if __name__ == "__main__":
    main()