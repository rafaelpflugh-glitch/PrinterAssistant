import json
from core.sniffer import FormSniffer


class FormScanner:


    def __init__(self, ip):

        self.ip = ip
        self.sniffer = FormSniffer(ip)



    def escanear(self, paginas):


        resultado = []


        print()

        print("==============================")
        print("ESCANEANDO FORMULÁRIOS")
        print("==============================")



        for pagina in paginas:


            try:

                forms = self.sniffer.analisar(
                    pagina
                )


                if forms:


                    print()

                    print("ENCONTRADO:")
                    print(pagina)

                    print(
                        len(forms),
                        "formulários"
                    )


                    resultado.append({

                        "pagina": pagina,

                        "forms": forms

                    })


            except Exception as erro:


                print(
                    "ERRO:",
                    pagina,
                    erro
                )



        return resultado




    def salvar(self, dados):


        with open(

            "database/forms_detectados.json",

            "w",

            encoding="utf-8"

        ) as arquivo:


            json.dump(

                dados,

                arquivo,

                indent=4,

                ensure_ascii=False

            )