import re



class UCFParser:


    def __init__(self):

        self.dados = {}



    def analisar(self, texto):


        linhas = texto.splitlines()


        for linha in linhas:


            linha = linha.strip()



            if not linha:
                continue



            if linha.startswith("//"):
                continue



            resultado = re.match(

                r'(.+?)\s+"(.*?)"',

                linha

            )



            if resultado:


                chave = resultado.group(1)

                valor = resultado.group(2)



                self.dados[chave] = valor



        return self.dados