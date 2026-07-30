import json
from pathlib import Path


# ============================================================
# PRINTER ASSISTANT - CONTEXT
# ============================================================
#
# Fonte central da impressora atualmente em atendimento.
#
# NÃO procura impressora.
# NÃO faz SNMP.
# NÃO faz PJL.
#
# Apenas lê a sessão ativa.
#
# Fluxo:
#
# scanner -> device -> session -> context
#
# Os demais módulos podem utilizar este módulo para saber
# qual equipamento está atualmente selecionado.
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

SESSION_FILE = BASE_DIR / "session.json"


# ============================================================
# ERRO DE CONTEXTO
# ============================================================

class NoActivePrinterError(Exception):
    """
    Não existe uma impressora ativa na sessão.
    """
    pass


# ============================================================
# CARREGAR SESSION.JSON
# ============================================================

def carregar_sessao():

    if not SESSION_FILE.exists():

        raise NoActivePrinterError(
            "Nenhuma sessão existe."
        )


    try:

        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(
                arquivo
            )

    except Exception as erro:

        raise NoActivePrinterError(
            f"Não foi possível ler a sessão: {erro}"
        )


    sessao = dados.get(
        "sessao"
    )


    if not sessao:

        raise NoActivePrinterError(
            "Arquivo de sessão inválido."
        )


    if not sessao.get(
        "ativa",
        False
    ):

        raise NoActivePrinterError(
            "Nenhuma impressora está ativa."
        )


    return sessao


# ============================================================
# IMPRESSORA ATIVA
# ============================================================

def obter_impressora_ativa():

    sessao = carregar_sessao()


    identificacao = sessao.get(
        "identificacao",
        {}
    )


    conectividade = sessao.get(
        "conectividade",
        {}
    )


    return {

        "ip":
            sessao.get(
                "ip"
            ),

        "nome":
            sessao.get(
                "nome"
            ),

        "fabricante":
            identificacao.get(
                "fabricante",
                "Desconhecido"
            ),

        "modelo":
            identificacao.get(
                "modelo",
                "Desconhecido"
            ),

        "familia":
            identificacao.get(
                "familia",
                ""
            ),

        "tipo":
            identificacao.get(
                "tipo",
                ""
            ),

        "serial":
            identificacao.get(
                "serial",
                "Desconhecido"
            ),

        "contador":
            identificacao.get(
                "contador"
            ),

        "conectividade":
            conectividade,

        "supplies":
            sessao.get(
                "supplies",
                []
            ),

        "estado":
            sessao.get(
                "estado",
                "OFFLINE"
            )

    }


# ============================================================
# IP DA IMPRESSORA ATIVA
# ============================================================

def obter_ip():

    impressora = obter_impressora_ativa()

    ip = impressora.get(
        "ip"
    )


    if not ip:

        raise NoActivePrinterError(
            "A sessão não possui IP."
        )


    return ip


# ============================================================
# TESTE
# ============================================================

def teste():

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE CONTEXT"
    )

    print("=" * 60)


    try:

        impressora = (
            obter_impressora_ativa()
        )


    except NoActivePrinterError as erro:

        print()

        print(
            "ERRO:",
            erro
        )

        return


    print()

    print(
        "IMPRESSORA ATIVA"
    )

    print("-" * 60)


    print(
        "IP:",
        impressora["ip"]
    )

    print(
        "Fabricante:",
        impressora["fabricante"]
    )

    print(
        "Modelo:",
        impressora["modelo"]
    )

    print(
        "Família:",
        impressora["familia"]
    )

    print(
        "Tipo:",
        impressora["tipo"]
    )

    print(
        "Serial:",
        impressora["serial"]
    )

    print(
        "Contador:",
        impressora["contador"]
    )

    print(
        "Estado:",
        impressora["estado"]
    )

    print(
        "Suprimentos:",
        len(
            impressora["supplies"]
        )
    )

    print()

    print(
        "Contexto carregado com sucesso."
    )

    print()

    print(
        "Arquivo:"
    )

    print(
        SESSION_FILE
    )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    teste()