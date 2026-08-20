"""
============================================================
PRINTER ASSISTANT
TERMINAL DE COMANDOS
============================================================

Interface temporária para executar comandos definidos em:

    database/commands.json

Fluxo:

    CLI
      ↓
    Commands
      ↓
    Executor
      ↓
    HTTPTool
      ↓
    Impressora

A CLI não conhece endpoints HTTP.
Os endpoints ficam exclusivamente no database/commands.json.
============================================================
"""

from __future__ import annotations

from core.session import Session
from core.commands import Commands


# ============================================================
# UTILITÁRIOS
# ============================================================

def linha():
    print("=" * 72)


def mostrar_resultado(
    nome,
    resultado,
):
    """
    Exibe o resultado retornado pelo Commands.

    O método aceita o formato atual do HTTPTool:
        success
        status_code
        url
        text

    e também trata erros.
    """

    print()
    linha()

    print(
        f"RESULTADO: {nome}"
    )

    linha()
    print()

    if not resultado:

        print(
            "[ERRO] Nenhum resultado retornado."
        )

        return

    if not isinstance(
        resultado,
        dict
    ):

        print(
            resultado
        )

        return

    sucesso = resultado.get(
        "success",
        False
    )

    if sucesso:

        print(
            "[OK] Comando executado."
        )

    else:

        print(
            "[ERRO] Comando não executado."
        )

    print()

    if "status_code" in resultado:

        print(
            f"HTTP........: "
            f"{resultado.get('status_code')}"
        )

    if "method" in resultado:

        print(
            f"Método......: "
            f"{resultado.get('method')}"
        )

    if "url" in resultado:

        print(
            f"URL.........: "
            f"{resultado.get('url')}"
        )

    if "content_type" in resultado:

        print(
            f"Content-Type: "
            f"{resultado.get('content_type')}"
        )

    texto = resultado.get(
        "text"
    )

    if texto:

        print()
        linha()

        print(
            "RESPOSTA"
        )

        linha()

        print(
            texto
        )

        linha()

    erro = resultado.get(
        "error"
    )

    if erro:

        print()

        print(
            f"Erro: {erro}"
        )


# ============================================================
# MENU
# ============================================================

def executar_menu(
    ip: str
):

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    session = Session()

    session.connect(
        ip
    )

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    comandos = Commands(
        session
    )

    # --------------------------------------------------------
    # MAPEAMENTO DO MENU
    # --------------------------------------------------------

    menu = {

        "1": (
            "printer_status",
            "Status da impressora"
        ),

        "2": (
            "print_configuration",
            "Relatório de configuração"
        ),

        "3": (
            "print_statistics",
            "Relatório de estatísticas"
        ),

    }

    # ========================================================
    # LOOP
    # ========================================================

    while True:

        print()

        linha()

        print(
            "PRINTER ASSISTANT - COMANDOS"
        )

        linha()

        print()

        print(
            f"Impressora selecionada: "
            f"{session.ip}"
        )

        print()

        print(
            "COMANDOS DISPONÍVEIS"
        )

        print()

        for numero, (
            nome,
            descricao
        ) in menu.items():

            print(
                f"[{numero}] "
                f"{descricao}"
            )

        print(
            "[0] Sair"
        )

        print()

        opcao = input(
            "Comando: "
        ).strip()

        # ----------------------------------------------------
        # SAIR
        # ----------------------------------------------------

        if opcao == "0":

            print()

            print(
                "Saindo do menu de comandos."
            )

            session.disconnect()

            return

        # ----------------------------------------------------
        # OPÇÃO INVÁLIDA
        # ----------------------------------------------------

        if opcao not in menu:

            print()

            print(
                "[ERRO] Opção inválida."
            )

            continue

        # ----------------------------------------------------
        # COMANDO
        # ----------------------------------------------------

        nome,
        descricao = menu[opcao]

        print()

        print(
            f"[EXEC] {descricao}"
        )

        print(
            f"[EXEC] Comando: {nome}"
        )

        # ----------------------------------------------------
        # EXECUÇÃO
        # ----------------------------------------------------

        resultado = comandos.executar(
            nome
        )

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        mostrar_resultado(
            nome,
            resultado
        )


# ============================================================
# MAIN
# ============================================================

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

        print()

        print(
            "IP não informado."
        )

        return

    executar_menu(
        ip
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    main()