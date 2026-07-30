from core.impressora import nova


def criar_objeto(dados, ip=None):


    impressora = nova()


    impressora["rede"]["ip"] = ip


    impressora["identificacao"]["serial"] = (
        dados.get("serial")
    )


    impressora["identificacao"]["firmware"] = (
        dados.get("firmware")
    )



    suprimentos = dados.get(
        "suprimentos",
        {}
    )



    impressora["suprimentos"]["imagem"]["serial"] = (
        suprimentos.get("unidade_serial")
    )

    impressora["suprimentos"]["imagem"]["paginas"] = (
        suprimentos.get("unidade_paginas")
    )

    impressora["suprimentos"]["imagem"]["nivel"] = (
        suprimentos.get("unidade_nivel")
    )



    impressora["suprimentos"]["toner"]["serial"] = (
        suprimentos.get("toner_serial")
    )

    impressora["suprimentos"]["toner"]["chip"] = (
        suprimentos.get("toner_chip")
    )

    impressora["suprimentos"]["toner"]["paginas"] = (
        suprimentos.get("toner_paginas")
    )

    impressora["suprimentos"]["toner"]["restante"] = (
        suprimentos.get("toner_restante")
    )

    impressora["suprimentos"]["toner"]["capacidade"] = (
        suprimentos.get("toner_capacidade")
    )

    impressora["suprimentos"]["toner"]["nivel"] = (
        suprimentos.get("toner_nivel")
    )


    return impressora