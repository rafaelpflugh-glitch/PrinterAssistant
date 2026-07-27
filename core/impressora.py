# ==================================================
# OBJETO IMPRESSORA
# ==================================================

import json
import os


ARQUIVO = "dados/contexto.json"



def nova():

    return {

        "identificacao": {

            "modelo": None,
            "serial": None,
            "firmware": None

        },

        "rede": {

            "ip": None

        },

        "suprimentos": {

            "toner": {

                "serial": None,
                "chip": None,
                "nivel": None,
                "paginas": None,
                "restante": None,
                "capacidade": None

            },


            "imagem": {

                "serial": None,
                "nivel": None,
                "paginas": None

            }

        }

    }





def salvar(impressora):


    pasta = os.path.dirname(ARQUIVO)


    if pasta and not os.path.exists(pasta):

        os.makedirs(pasta)



    with open(

        ARQUIVO,

        "w",

        encoding="utf-8"

    ) as arquivo:


        json.dump(

            impressora,

            arquivo,

            indent=4,

            ensure_ascii=False

        )





def carregar():


    try:


        with open(

            ARQUIVO,

            "r",

            encoding="utf-8"

        ) as arquivo:


            return json.load(arquivo)



    except:


        return nova()