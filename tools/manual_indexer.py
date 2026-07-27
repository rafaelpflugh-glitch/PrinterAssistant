import os
import json
import fitz   # PyMuPDF



PASTA_MANUAIS = "manuals"

PASTA_KNOWLEDGE = "knowledge"

ARQUIVO_BANCO = os.path.join(
    PASTA_KNOWLEDGE,
    "manuals.json"
)




def criar_pasta():

    if not os.path.exists(PASTA_KNOWLEDGE):

        os.makedirs(
            PASTA_KNOWLEDGE
        )




def extrair_modelos(nome):


    modelos = []


    texto = nome.upper()


    palavras = texto.replace(
        ",",
        " "
    ).replace(
        ".",
        " "
    ).split()



    for palavra in palavras:


        if (
            palavra.startswith("MX")
            or
            palavra.startswith("MS")
            or
            palavra.startswith("XM")
            or
            palavra.startswith("B")
            or
            palavra.startswith("M")
        ):

            modelos.append(
                palavra
            )


    return list(
        set(modelos)
    )





def indexar_manuais():


    criar_pasta()


    if not os.path.exists(
        PASTA_MANUAIS
    ):


        return "Pasta manuals não encontrada."



    banco = []



    arquivos = [

        arquivo

        for arquivo in os.listdir(
            PASTA_MANUAIS
        )

        if arquivo.lower().endswith(".pdf")

    ]



    if not arquivos:


        return "Nenhum PDF encontrado."





    for arquivo in arquivos:


        caminho = os.path.join(
            PASTA_MANUAIS,
            arquivo
        )


        print(
            f"Indexando: {arquivo}"
        )


        modelos = extrair_modelos(
            arquivo
        )


        try:


            documento = fitz.open(
                caminho
            )


            total_paginas = len(
                documento
            )


            print(
                f"Páginas: {total_paginas}"
            )



            for numero, pagina in enumerate(
                documento
            ):


                texto = pagina.get_text()



                if texto.strip():


                    registro = {


                        "arquivo":
                        arquivo,


                        "pagina":
                        numero + 1,


                        "modelos":
                        modelos,


                        "texto":
                        texto

                    }



                    banco.append(
                        registro
                    )



            documento.close()



        except Exception as erro:


            print(
                f"Erro lendo {arquivo}: {erro}"
            )





    with open(
        ARQUIVO_BANCO,
        "w",
        encoding="utf-8"
    ) as arquivo:


        json.dump(

            banco,

            arquivo,

            indent=4,

            ensure_ascii=False

        )





    return f"""
Indexação concluída.

PDFs encontrados:
{len(arquivos)}

Páginas indexadas:
{len(banco)}

Banco criado:

{ARQUIVO_BANCO}

"""
