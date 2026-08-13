"""
Printer Assistant - Terminal de Comandos

Interface temporária para executar ações
sobre a impressora selecionada.
"""

from __future__ import annotations

from core.commands.printer_commands import PrinterCommands


def linha():
    print("=" * 72)


def executar_menu(ip: str):

    comandos = PrinterCommands(
        ip
    )

    while True:

        print()

        linha()

        print(
            "PRINTER ASSISTANT - COMANDOS"
        )

        linha()

        print(
            f"Impressora selecionada: {ip}"
        )

        print()

        for item in comandos.listar_comandos():

            print(
                f"{item['id']} - {item['nome']}"
            )

        print()

        opcao = input(
            "Comando: "
        ).strip()

        if opcao == "0":

            print()
            print(
                "Saindo do menu de comandos."
            )

            return

        resultado = comandos.executar(
            opcao
        )

        print()

        if resultado.sucesso:

            print(
                "[OK]",
                resultado.mensagem,
            )

        else:

            print(
                "[ERRO]",
                resultado.mensagem,
            )

        if resultado.resposta:

            print()

            print(
                "-" * 72
            )

            print(
                resultado.resposta
            )

            print(
                "-" * 72
            )


def main():

    print()

    linha()

    print(
        "PRINTER ASSISTANT"
    )

    print(
        "MENU DE COMANDOS"
    )

    linha()

    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP não informado."
        )

        return

    executar_menu(
        ip
    )


if __name__ == "__main__":

    main()