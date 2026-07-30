from core.banco import carregar



def listar():

    banco = carregar()


    if not banco:

        return """

=========== BANCO LEXMARK ===========

Nenhuma impressora cadastrada.

=====================================

"""


    texto = """

=========== BANCO LEXMARK ===========

"""


    contador = 1


    for serial, impressora in banco.items():


        ident = impressora.get(
            "identificacao",
            {}
        )


        rede = impressora.get(
            "rede",
            {}
        )


        suprimentos = impressora.get(
            "suprimentos",
            {}
        )


        toner = suprimentos.get(
            "toner",
            {}
        )


        imagem = suprimentos.get(
            "imagem",
            {}
        )



        texto += f"""

{contador})

Modelo:
{ident.get('modelo')}

Serial:
{serial}

IP:
{rede.get('ip')}

Firmware:
{ident.get('firmware')}


TONER

Serial:
{toner.get('serial')}

Nível:
{toner.get('nivel')}%


UNIDADE DE IMAGEM

Serial:
{imagem.get('serial')}

Nível:
{imagem.get('nivel')}%


-------------------------------------

"""


        contador += 1



    texto += """

=====================================

"""


    return texto