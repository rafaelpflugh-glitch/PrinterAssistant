import os



ARQUIVO = (
    "knowledge/banco_manual.txt"
)





def consultar(pergunta):


    if not os.path.exists(
        ARQUIVO
    ):


        return (
            "Nenhum manual indexado."
        )



    with open(
        ARQUIVO,
        "r",
        encoding="utf-8"
    ) as arquivo:


        texto = arquivo.read()



    palavras = pergunta.lower().split()



    encontrados = []



    for linha in texto.splitlines():


        linha_lower = linha.lower()



        for palavra in palavras:


            if palavra in linha_lower:

                encontrados.append(
                    linha
                )

                break



    if not encontrados:


        return (
            "Nenhuma informação encontrada nos manuais."
        )



    return "\n".join(
        encontrados[:50]
    )