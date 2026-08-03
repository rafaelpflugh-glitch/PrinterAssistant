def extrair_pagecount(resposta):

    if not resposta:
        return None


    linhas = resposta.splitlines()


    for linha in linhas:

        linha = linha.strip()


        if linha.isdigit():

            return int(linha)


    return None