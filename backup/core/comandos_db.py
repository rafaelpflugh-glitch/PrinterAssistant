import json
import os


BASE = "database/comandos"



def carregar(nome):

    arquivo = os.path.join(
        BASE,
        nome + ".json"
    )


    if not os.path.exists(arquivo):

        return None



    codificacoes = [
        "utf-8-sig",
        "utf-8",
        "cp1252"
    ]


    for codificacao in codificacoes:

        try:

            with open(
                arquivo,
                "r",
                encoding=codificacao
            ) as f:

                return json.load(f)


        except (UnicodeDecodeError, json.JSONDecodeError):

            continue



    print(
        "Falha ao carregar:",
        arquivo
    )


    return None