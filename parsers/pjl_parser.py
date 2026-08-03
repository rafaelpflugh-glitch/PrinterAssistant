class PJLParser:


    @staticmethod
    def pagecount(resposta):

        linhas = resposta.splitlines()


        for linha in linhas:

            linha = linha.strip()


            if linha.isdigit():

                return int(linha)


        return None



    @staticmethod
    def status(resposta):

        dados = {}


        for linha in resposta.splitlines():

            linha = linha.strip()


            if "=" in linha:

                chave, valor = linha.split(
                    "=",
                    1
                )


                dados[chave.lower()] = valor.strip(
                    '"'
                )


        return dados