"""
Printer Assistant
PJL PageCount Parser
"""


def parse(texto):

    if not texto:
        return None

    for linha in texto.splitlines():

        linha = linha.strip()

        if linha.isdigit():

            return {

                "pagecount": int(linha)

            }

    return {

        "pagecount": None

    }