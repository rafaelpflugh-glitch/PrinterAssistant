"""
Printer Assistant
PJL Memory Parser
"""


def parse(texto):

    resultado = {}

    if not texto:
        return resultado

    for linha in texto.splitlines():

        linha = linha.strip()

        if "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)

        chave = chave.strip().lower()

        valor = valor.strip()

        try:
            valor = int(valor)

        except Exception:
            pass

        resultado[chave] = valor

    return resultado