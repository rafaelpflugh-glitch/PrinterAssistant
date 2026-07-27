import re



def extrair_campo(padrao, texto):

    resultado = re.search(
        padrao,
        texto,
        re.IGNORECASE | re.MULTILINE
    )


    if resultado:

        return (
            resultado
            .group(1)
            .strip()
            .replace(",", "")
        )


    return "Não encontrado"





def extrair_suprimentos(dados):


    resultado = {


        "unidade_serial": "Não encontrado",
        "unidade_paginas": "Não encontrado",
        "unidade_nivel": "Não encontrado",


        "toner_serial": "Não encontrado",
        "toner_chip": "Não encontrado",
        "toner_paginas": "Não encontrado",
        "toner_restante": "Não encontrado",
        "toner_capacidade": "Não encontrado",
        "toner_nivel": "Não encontrado"

    }



    # ==========================
    # UNIDADE DE IMAGEM
    # ==========================


    bloco_iu = re.search(

        r"Mono Cartridge Imaging Unit(.*?)(?=Black Toner|$)",

        dados,

        re.IGNORECASE | re.DOTALL

    )



    if bloco_iu:


        bloco = bloco_iu.group(1)



        resultado["unidade_serial"] = extrair_campo(

            r"S/N:\s*(\S+)",

            bloco

        )



        resultado["unidade_paginas"] = extrair_campo(

            r"IU Page Count;\s*(\d+)",

            bloco

        )



        resultado["unidade_nivel"] = extrair_campo(

            r"Current Level\s*=\s*(\d+)",

            bloco

        )





    # ==========================
    # TONER PRETO
    # ==========================


    bloco_toner = re.search(

        r"Black Toner(.*?)(?=Mono Cartridge Imaging Unit|$)",

        dados,

        re.IGNORECASE | re.DOTALL

    )



    if bloco_toner:


        bloco = bloco_toner.group(1)



        resultado["toner_serial"] = extrair_campo(

            r"serial\s+(\S+)",

            bloco

        )



        resultado["toner_chip"] = extrair_campo(

            r"partNumber\s+(\S+)",

            bloco

        )



        resultado["toner_paginas"] = extrair_campo(

            r"pageCount\s+(\d+)",

            bloco

        )



        resultado["toner_restante"] = extrair_campo(

            r"pageRemain\s+(\d+)",

            bloco

        )



        resultado["toner_capacidade"] = extrair_campo(

            r"maxCapacity\s+(\d+)",

            bloco

        )



        resultado["toner_nivel"] = extrair_campo(

            r"level\s+(\d+)",

            bloco

        )



    return resultado





def formatar(resultado):


    return f"""

=========== SUPRIMENTOS LEXMARK ===========


UNIDADE DE IMAGEM

Serial:
{resultado['unidade_serial']}

Páginas:
{resultado['unidade_paginas']}

Nível:
{resultado['unidade_nivel']}%



TONER PRETO

Serial:
{resultado['toner_serial']}

ID CHIP:
{resultado['toner_chip']}

Páginas:
{resultado['toner_paginas']}

Restante:
{resultado['toner_restante']}

Capacidade:
{resultado['toner_capacidade']}

Nível:
{resultado['toner_nivel']}%


============================================

"""