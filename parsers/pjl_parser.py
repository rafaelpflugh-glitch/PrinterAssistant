"""
Printer Assistant

PJL Parser

Converte respostas PJL brutas em dados estruturados.

"""


class PJLParser:



    @staticmethod
    def pagecount(texto):


        if not texto:

            return None



        for linha in texto.splitlines():


            linha = linha.strip()


            if linha.isdigit():

                return int(linha)



        return None





    @staticmethod
    def status(texto):


        resultado = {}



        if not texto:

            return resultado




        for linha in texto.splitlines():


            linha = linha.strip()



            if "=" not in linha:

                continue



            chave, valor = linha.split(

                "=",

                1

            )



            chave = chave.strip().lower()

            valor = valor.strip()



            if valor.lower() == "true":

                valor = True



            elif valor.lower() == "false":

                valor = False



            resultado[chave] = valor



        return resultado





    @staticmethod
    def memory(texto):


        resultado = {}



        if not texto:

            return resultado




        for linha in texto.splitlines():


            linha = linha.strip()



            if "=" not in linha:

                continue




            chave, valor = linha.split(

                "=",

                1

            )



            chave = chave.strip().lower()

            valor = valor.strip()



            try:

                valor = int(valor)


            except ValueError:

                pass




            resultado[chave] = valor



        return resultado





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