"""
Printer Assistant - Capability Discovery CLI

Mostra o mapa de capacidades PJL descoberto
automaticamente da impressora.

ATENÇÃO:

Este programa NÃO escreve configurações.
Ele apenas consulta INFO ID / CONFIG / VARIABLES.
"""

from core.commands.config._discover import (
    PJLCapabilityDiscovery,
)


SEPARADOR = "=" * 72


def imprimir_titulo(titulo):

    print()
    print(SEPARADOR)
    print(titulo)
    print(SEPARADOR)


def main():

    print(SEPARADOR)
    print("PRINTER ASSISTANT - PJL CAPABILITY DISCOVERY")
    print(SEPARADOR)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    discovery = PJLCapabilityDiscovery(
        ip,
        porta=9100,
        timeout=5,
    )

    try:

        print()
        print(
            f"Conectando em {ip}:9100..."
        )

        discovery.conectar()

        print("Conectado.")

        capacidades = discovery.descobrir()

        # ==================================================
        # IDENTIDADE
        # ==================================================

        imprimir_titulo(
            "1. IDENTIDADE"
        )

        print(
            f"Modelo   : "
            f"{capacidades.modelo}"
        )

        print(
            f"Serial   : "
            f"{capacidades.serial}"
        )

        print(
            f"Firmware : "
            f"{capacidades.firmware}"
        )

        # ==================================================
        # RESUMO
        # ==================================================

        imprimir_titulo(
            "2. RESUMO DAS CAPACIDADES"
        )

        todas = capacidades.todas()

        gravaveis = (
            capacidades.gravaveis_candidatas()
        )

        readonly = (
            capacidades.readonly()
        )

        print(
            f"Variáveis descobertas : "
            f"{len(todas)}"
        )

        print(
            f"Candidatas a escrita  : "
            f"{len(gravaveis)}"
        )

        print(
            f"Somente leitura       : "
            f"{len(readonly)}"
        )

        # ==================================================
        # FAMÍLIAS
        # ==================================================

        imprimir_titulo(
            "3. FAMÍLIAS"
        )

        familias = {}

        for variavel in todas:

            familias.setdefault(
                variavel.familia,
                0,
            )

            familias[
                variavel.familia
            ] += 1

        for familia, quantidade in sorted(
            familias.items()
        ):
            print(
                f"{familia:<25} "
                f"{quantidade}"
            )

        # ==================================================
        # VARIÁVEIS
        # ==================================================

        imprimir_titulo(
            "4. VARIÁVEIS DESCOBERTAS"
        )

        for variavel in todas:

            print()
            print(
                f"[{variavel.familia}] "
                f"{variavel.nome}"
            )

            print(
                f"  atual   : "
                f"{variavel.valor}"
            )

            print(
                f"  tipo    : "
                f"{variavel.tipo}"
            )

            print(
                f"  readonly: "
                f"{variavel.readonly}"
            )

            if variavel.valores:

                print(
                    "  valores : "
                    + ", ".join(
                        variavel.valores
                    )
                )

            if (
                variavel.minimo is not None
                or variavel.maximo is not None
            ):

                print(
                    f"  range   : "
                    f"{variavel.minimo} "
                    f"-> "
                    f"{variavel.maximo}"
                )

        # ==================================================
        # CANDIDATAS A ESCRITA
        # ==================================================

        imprimir_titulo(
            "5. CANDIDATAS A ESCRITA"
        )

        print(
            "Estas variáveis NÃO estão marcadas "
            "como READONLY."
        )

        print(
            "Ainda não significa que DEFAULT "
            "seja permitido."
        )

        for variavel in gravaveis:

            print(
                f"{variavel.nome:<40} "
                f"{variavel.valor}"
            )

        # ==================================================
        # READONLY
        # ==================================================

        imprimir_titulo(
            "6. SOMENTE LEITURA"
        )

        for variavel in readonly:

            print(
                f"{variavel.nome:<40} "
                f"{variavel.valor}"
            )

        # ==================================================
        # IDIOMA
        # ==================================================

        imprimir_titulo(
            "7. IDIOMA"
        )

        lang = capacidades.obter(
            "LANG"
        )

        if lang:

            print(
                f"Atual: {lang.valor}"
            )

            print(
                "Aceitos:"
            )

            for valor in lang.valores:

                print(
                    f"  - {valor}"
                )

        else:

            print(
                "LANG não encontrada."
            )

        # ==================================================
        # FINAL
        # ==================================================

        imprimir_titulo(
            "DESCOBERTA CONCLUÍDA"
        )

        print(
            "Nenhuma configuração foi alterada."
        )

    except Exception as erro:

        print()
        print(
            "ERRO DURANTE A DESCOBERTA:"
        )

        print(
            repr(erro)
        )

    finally:

        discovery.fechar()

        print()
        print(
            "Conexão RAW encerrada."
        )


if __name__ == "__main__":
    main()