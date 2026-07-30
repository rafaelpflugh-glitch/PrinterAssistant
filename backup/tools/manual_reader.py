import os

from pypdf import PdfReader



PASTA_MANUAIS = "manuals"



PASTA_KNOWLEDGE = "knowledge"



ARQUIVO = (
    "knowledge/banco_manual.txt"
)





def ler_pdf(caminho):


    texto = ""


    try:

        pdf = PdfReader(
            caminho
        )


        for pagina in pdf.pages:

            conteudo = pagina.extract_text()


            if conteudo:

                texto += conteudo + "\n"



    except Exception as erro:


        texto = (
            f"Erro lendo PDF: {erro}"
        )



    return texto






def indexar_manuaIs():


    if not os.path.exists(
        PASTA_KNOWLEDGE
    ):

        os.makedirs(
            PASTA_KNOWLEDGE
        )



    banco = ""



    for arquivo in os.listdir(
        PASTA_MANUAIS
    ):


        if arquivo.lower().endswith(
            ".pdf"
        ):


            caminho = os.path.join(
                PASTA_MANUAIS,
                arquivo
            )


            print(
                "Lendo:",
                arquivo
            )


            texto = ler_pdf(
                caminho
            )


            banco += (

                "\n\n====================\n"

                + arquivo +

                "\n====================\n"

                + texto

            )




    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as arquivo:


        arquivo.write(
            banco
        )



    return (

        "Indexação concluída.\n"

        f"Tamanho: {len(banco)} caracteres"

    )