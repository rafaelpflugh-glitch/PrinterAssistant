from core.contexto import obter_contexto



def analisar():



    contexto = obter_contexto()


    if not contexto:


        return """

Nenhuma impressora selecionada.

"""



    suprimentos = contexto.get(
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



    analise = []



    # ==========================
    # TONER
    # ==========================


    try:

        nivel_toner = int(
            toner.get("nivel",0)
        )


        if nivel_toner > 50:

            analise.append(
                "✓ Toner em bom estado."
            )


        elif nivel_toner > 20:

            analise.append(
                "⚠ Toner próximo da metade."
            )


        else:

            analise.append(
                "✘ Toner baixo."
            )


    except:


        pass




    # ==========================
    # UNIDADE DE IMAGEM
    # ==========================


    try:

        nivel_imagem = int(
            imagem.get("nivel",0)
        )


        if nivel_imagem > 70:


            analise.append(
                "✓ Unidade de imagem em bom estado."
            )


        elif nivel_imagem > 30:


            analise.append(
                "⚠ Unidade de imagem com desgaste moderado."
            )


        else:


            analise.append(
                "✘ Unidade de imagem próxima do fim."
            )


    except:


        pass





    return f"""

=========================================================
                 ANÁLISE TÉCNICA
=========================================================


MODELO:
{contexto.get("modelo")}


SERIAL:
{contexto.get("serial")}


FIRMWARE:
{contexto.get("firmware")}



=========================================================
RESULTADO
=========================================================


{chr(10).join(analise)}



=========================================================

"""