class ConfigInterpreter:


    def __init__(self, dados):

        self.dados = dados



    def obter(self, chave):

        return self.dados.get(chave)



    def interpretar(self):


        resultado = {}



        resultado["Idioma"] = self.idioma()


        resultado["Duplex"] = self.duplex()


        resultado["Copias"] = self.obter(

            "print.numberOfCopies"

        )


        resultado["Timeout"] = self.obter(

            "printTimeout"

        )



        return resultado





    def idioma(self):


        idiomas = {


            "0": "English",

            "1": "Deutsch",

            "2": "Francais",

            "4": "Espanol",

            "5": "Italiano",

            "16": "Português"

        }



        valor = self.obter(

            "language"

        )


        return idiomas.get(

            valor,

            valor

        )





    def duplex(self):


        valores = {


            "0": "Desativado",

            "1": "Ativado"

        }



        valor = self.obter(

            "print.duplex.bindingEdge"

        )


        return valores.get(

            valor,

            valor

        )