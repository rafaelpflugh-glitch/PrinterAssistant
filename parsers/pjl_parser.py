"""
Printer Assistant
PJL Parser

Converte respostas PJL em estruturas Python.

Todas as ferramentas PJL utilizam este parser.
"""


class PJLParser:

    @staticmethod
    def _convert(value):

        value = value.strip()

        upper = value.upper()

        if upper in ("TRUE", "ON"):
            return True

        if upper in ("FALSE", "OFF"):
            return False

        try:
            return int(value)
        except ValueError:
            pass

        return value


    @classmethod
    def key_value(cls, texto):

        resultado = {}

        if not texto:
            return resultado


        for linha in texto.splitlines():

            linha = linha.strip()


            if not linha:
                continue


            if linha.startswith("@PJL"):
                continue


            if "=" not in linha:
                continue


            chave, valor = linha.split("=",1)


            chave = chave.strip().lower()

            resultado[chave] = cls._convert(valor)


        return resultado



    @staticmethod
    def pagecount(texto):

        if not texto:
            return None


        for linha in texto.splitlines():

            linha = linha.strip()


            if linha.isdigit():

                return int(linha)


        return None



    @classmethod
    def status(cls,texto):

        return cls.key_value(texto)



    @classmethod
    def memory(cls,texto):

        return cls.key_value(texto)



    @classmethod
    def config(cls,texto):

        return cls.key_value(texto)



    @classmethod
    def variables(cls,texto):

        return cls.key_value(texto)



    @classmethod
    def prodinfo(cls,texto):

        return cls.key_value(texto)



    @staticmethod
    def info_id(texto):

        if not texto:

            return None


        for linha in texto.splitlines():

            linha = linha.strip()


            if linha.startswith('"'):

                return linha.replace('"',"").strip()


        return texto.strip()



    @staticmethod
    def raw(texto):

        if texto is None:

            texto=""


        return {

            "raw_size":len(texto),

            "preview":texto[:300],

            "raw":texto

        }



    @classmethod
    def generic(cls,texto):

        dados = cls.key_value(texto)


        if dados:

            return dados


        return cls.raw(texto)