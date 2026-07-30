import json
import os



# ==================================================
# ARQUIVO DE MEMÓRIA
# ==================================================

ARQUIVO_CONTEXTO = "dados/contexto.json"




# ==================================================
# CONTEXTO PADRÃO
# ==================================================

contexto_atual = {


    "ip": None,

    "modelo": None,

    "serial": None,

    "firmware": None,

    "ultimo_debug": None,

    "ultimo_diagnostico": None,

    "suprimentos": None

}




# ==================================================
# CARREGAR CONTEXTO
# ==================================================

def carregar():


    global contexto_atual


    try:


        if os.path.exists(ARQUIVO_CONTEXTO):


            with open(
                ARQUIVO_CONTEXTO,
                "r",
                encoding="utf-8"
            ) as arquivo:


                dados = json.load(
                    arquivo
                )


                contexto_atual.update(
                    dados
                )


    except Exception:


        pass







# ==================================================
# SALVAR CONTEXTO
# ==================================================

def salvar():


    try:


        pasta = os.path.dirname(
            ARQUIVO_CONTEXTO
        )


        if pasta and not os.path.exists(pasta):

            os.makedirs(pasta)



        with open(
            ARQUIVO_CONTEXTO,
            "w",
            encoding="utf-8"
        ) as arquivo:


            json.dump(

                contexto_atual,

                arquivo,

                indent=4,

                ensure_ascii=False

            )


    except Exception:


        pass







# ==================================================
# ATUALIZAR DADOS
# ==================================================

def atualizar(dados):


    global contexto_atual



    for chave, valor in dados.items():


        contexto_atual[chave] = valor



    salvar()







# ==================================================
# OBTER CONTEXTO
# ==================================================

def obter_contexto():


    return contexto_atual.copy()







# ==================================================
# LIMPAR
# ==================================================

def limpar():


    global contexto_atual


    contexto_atual = {


        "ip": None,

        "modelo": None,

        "serial": None,

        "firmware": None,

        "ultimo_debug": None,

        "ultimo_diagnostico": None,

        "suprimentos": None

    }


    salvar()







# Carrega ao importar o módulo

carregar()