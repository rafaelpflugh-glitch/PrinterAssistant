import re


def dividir_secoes(texto):

    secoes = {}

    linhas = texto.splitlines()

    titulo = "INICIO"

    conteudo = []

    for linha in linhas:

        linha_limpa = linha.strip()

        # início de seção
        if (
            linha_limpa.startswith("---------------")
            and linha_limpa.endswith("---------------")
        ):

            if conteudo:

                secoes[titulo] = "\n".join(conteudo).strip()

            titulo = (
                linha_limpa
                .replace("-", "")
                .strip()
            )

            conteudo = []

            continue

        conteudo.append(linha)

    if conteudo:

        secoes[titulo] = "\n".join(conteudo).strip()

    return secoes