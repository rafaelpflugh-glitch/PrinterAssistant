"""
Printer Assistant
PJL Parser

Converte respostas PJL brutas em dados utilizáveis.

"""


class PJLParser:


    # ======================================================
    # PAGECOUNT
    # ======================================================

    @staticmethod
    def pagecount(texto):

        if not texto:
            return None


        linhas = texto.splitlines()


        for linha in linhas:

            linha = linha.strip()


            if linha.isdigit():

                return int(linha)


        return None



    # ======================================================
    # STATUS
    # ======================================================

    @staticmethod
    def status(texto):

        resultado = {}


        if not texto:
            return resultado


        linhas = texto.splitlines()


        for linha in linhas:

            linha = linha.strip()


            if "=" not in linha:
                continue


            chave, valor = linha.split(
                "=",
                1
            )


            chave = chave.strip().lower()

            valor = valor.strip()


            if valor == "TRUE":

                valor = True


            elif valor == "FALSE":

                valor = False


            resultado[chave] = valor



        return resultado



    # ======================================================
    # MEMORY
    # ======================================================

    @staticmethod
    def memory(texto):

        resultado = {}


        if not texto:
            return resultado


        linhas = texto.splitlines()


        for linha in linhas:

            if "=" not in linha:
                continue


            chave, valor = linha.split(
                "=",
                1
            )


            try:

                valor = int(valor)

            except:

                pass


            resultado[
                chave.lower()
            ] = valor



        return resultado



    # ======================================================
    # INFO ID
    # ======================================================

    @staticmethod
    def info_id(texto):

        if not texto:
            return None


        for linha in texto.splitlines():

            linha = linha.strip()


            if linha.startswith('"'):

                return linha.replace(
                    '"',
                    ""
                )


        return texto.strip()