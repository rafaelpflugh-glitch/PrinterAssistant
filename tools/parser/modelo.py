import json



def identificar_modelo(dados):


    try:

        with open(
            "database/models/identificacao.json",
            "r",
            encoding="utf-8"
        ) as arquivo:

            banco = json.load(arquivo)


    except Exception:

        return {

            "modelo": None,

            "confianca": 0

        }



    for item in banco["modelos"]:


        pontos = 0



        if dados.get("board") == item.get("board"):

            pontos += 40



        if dados.get("hardware") == item.get("hardware"):

            pontos += 40



        if dados.get("firmware","").startswith(
            item.get("firmware_prefix")
        ):

            pontos += 20



        if pontos >= 80:

            return {

                "modelo": item["modelo"],

                "confianca": pontos

            }



    return {

        "modelo": None,

        "confianca": 0

    }