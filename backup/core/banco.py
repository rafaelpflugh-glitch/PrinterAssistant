import json
import os


ARQUIVO = "database/impressoras.json"



def carregar():

    if not os.path.exists(ARQUIVO):

        return {}


    with open(
        ARQUIVO,
        "r",
        encoding="utf-8"
    ) as arquivo:

        return json.load(arquivo)





def salvar(dados):


    pasta = os.path.dirname(ARQUIVO)


    if not os.path.exists(pasta):

        os.makedirs(pasta)



    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as arquivo:


        json.dump(
            dados,
            arquivo,
            indent=4,
            ensure_ascii=False
        )





def salvar_impressora(impressora):


    banco = carregar()


    serial = (
        impressora
        ["identificacao"]
        ["serial"]
    )


    if not serial:

        return False



    banco[serial] = impressora


    salvar(banco)


    return True





def buscar(serial):


    banco = carregar()


    return banco.get(serial)