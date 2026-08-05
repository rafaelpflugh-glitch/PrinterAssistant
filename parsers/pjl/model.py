"""
Printer Assistant
PJL Model Parser
"""


def parse(texto):

    if not texto:
        return {

            "model": None

        }

    for linha in texto.splitlines():

        linha = linha.strip()

        if linha.startswith('"'):

            return {

                "model": linha.replace('"', "")

            }

    return {

        "model": texto.strip()

    }