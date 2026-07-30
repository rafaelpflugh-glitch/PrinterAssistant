from core.contexto import obter_contexto
from tools.conversor import criar_objeto
from core.banco import salvar_impressora



def salvar_atual():


    dados = obter_contexto()


    if not dados.get("serial"):

        return False



    objeto = criar_objeto(

        dados,

        dados.get("ip")

    )


    return salvar_impressora(
        objeto
    )