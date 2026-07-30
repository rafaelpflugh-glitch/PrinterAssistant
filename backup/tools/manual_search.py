import os
import json



ARQUIVO_BANCO = (
    "knowledge/manuals.json"
)





def buscar_manual(pergunta, limite=5):


    if not os.path.exists(
        ARQUIVO_BANCO
    ):


        return """

Banco de manuais não encontrado.

Execute:

indexar_manuais()

"""



    with open(
        ARQUIVO_BANCO,
        "r",
        encoding="utf-8"
    ) as arquivo:


        manuais = json.load(
            arquivo
        )




    palavras = (
        pergunta
        .lower()
        .split()
    )



    resultados = []



    for pagina in manuais:


        texto = pagina.get(
            "texto",
            ""
        ).lower()



        pontuacao = 0



        for palavra in palavras:


            if palavra in texto:


                pontuacao += 1



                # palavras importantes
                if len(palavra) >= 4:

                    pontuacao += 1




        if pontuacao > 0:


            resultados.append({

                "pontuacao":
                pontuacao,


                "arquivo":
                pagina.get(
                    "arquivo",
                    "desconhecido"
                ),


                "pagina":
                pagina.get(
                    "pagina",
                    "?"
                ),


                "texto":
                pagina.get(
                    "texto",
                    ""
                )[:1000]

            })





    if not resultados:


        return """

Nenhuma informação encontrada
nos manuais.

"""




    resultados.sort(

        key=lambda x:
        x["pontuacao"],

        reverse=True

    )




    resposta = []



    for item in resultados[:limite]:


        resposta.append(

f"""
=================================

Manual:

{item['arquivo']}


Página:

{item['pagina']}


Relevância:

{item['pontuacao']}



Trecho:

{item['texto']}

"""

        )



    return "\n".join(
        resposta
    )