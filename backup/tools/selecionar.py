from core.contexto import atualizar
from core.contexto import obter_contexto

from tools.salvar_automatico import salvar_atual




# ==================================================
# SELECIONAR IMPRESSORA
# ==================================================

def selecionar(numero):


    contexto = obter_contexto()


    impressoras = contexto.get(
        "impressoras_encontradas",
        []
    )



    if not impressoras:


        return """

Nenhuma busca de impressoras realizada.

Use:

procurar impressoras

"""



    try:

        indice = int(numero) - 1


    except:


        return """

Número inválido.

Use:

selecionar 1

ou

selecionar 2

"""





    if indice < 0 or indice >= len(impressoras):


        return """

Impressora inexistente.

"""





    impressora = impressoras[indice]





    # ==================================
    # ATUALIZA MEMÓRIA ATUAL
    # ==================================


    atualizar({

        "ip":

        impressora.get(
            "ip"
        ),


        "serial":

        impressora.get(
            "serial"
        ),


        "modelo":

        impressora.get(
            "modelo"
        ),


        "firmware":

        impressora.get(
            "firmware"
        )

    })





    # ==================================
    # SALVA NO BANCO PERMANENTE
    # ==================================


    banco = salvar_atual()





    if banco:


        mensagem_banco = """

Banco:

IMPRESSORA SALVA COM SUCESSO

"""


    else:


        mensagem_banco = """

Banco:

Não foi possível salvar.

"""





    return f"""

=================================

IMPRESSORA SELECIONADA

=================================


IP:

{impressora.get('ip')}


Modelo:

{impressora.get('modelo')}


Serial:

{impressora.get('serial')}


Firmware:

{impressora.get('firmware')}


{mensagem_banco}


=================================

"""