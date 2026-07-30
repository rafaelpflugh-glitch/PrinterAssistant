import json
import os
from datetime import datetime


ARQUIVO = "memoria_historico.json"



# ==================================================
# SALVAR EVENTO TÉCNICO
# ==================================================

def salvar(evento):


    historico = ler()



    registro = {

        "data":

        datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        ),


        "evento":

        evento

    }



    historico.append(
        registro
    )



    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as arquivo:


        json.dump(

            historico,

            arquivo,

            indent=4,

            ensure_ascii=False

        )





# ==================================================
# LER HISTÓRICO
# ==================================================

def ler():


    if not os.path.exists(
        ARQUIVO
    ):


        return []



    try:


        with open(

            ARQUIVO,

            "r",

            encoding="utf-8"

        ) as arquivo:


            return json.load(
                arquivo
            )


    except:


        return []





# ==================================================
# ÚLTIMOS EVENTOS
# ==================================================

def ultimos(limite=10):


    historico = ler()



    return historico[-limite:]





# ==================================================
# LIMPAR HISTÓRICO
# ==================================================

def limpar():


    with open(

        ARQUIVO,

        "w",

        encoding="utf-8"

    ) as arquivo:


        json.dump(

            [],

            arquivo,

            indent=4

        )