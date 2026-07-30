import requests

from tools.debug import coletar_debug


class PrinterDetector:



    def __init__(self, printer):

        self.printer = printer



    def identificar(self):


        endpoints = [

            "/",

            "/cgi-bin/dynamic/printer/PrinterStatus.html",

            "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",

            "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html"

        ]



        headers = {

            "User-Agent":
            "Mozilla/5.0"

        }



        for endpoint in endpoints:


            try:


                url = (
                    f"http://{self.printer.ip}"
                    f"{endpoint}"
                )


                resposta = requests.get(

                    url,

                    headers=headers,

                    timeout=5

                )



                if resposta.status_code != 200:

                    continue



                texto = resposta.text



                indicadores = [

                    "lexmark",

                    "printer",

                    "printerstatus",

                    "toner",

                    "supplies",

                    "deviceinfo"

                ]



                if any(
                    x.lower() in texto.lower()
                    for x in indicadores
                ):


                    print(
                        f"    EWS encontrado: {endpoint}"
                    )


                    self.printer.hostname = (
                        self.printer.ip
                    )


                    self.coletar_debug()


                    return True



            except Exception:


                pass



        return False




    def coletar_debug(self):


        try:


            dados = coletar_debug(
                self.printer.ip
            )


            if dados:

                self.extrair(dados)



        except Exception:


            pass




    def extrair(self,texto):


        linhas = texto.splitlines()



        for linha in linhas:


            l = linha.lower()



            if "model" in l:

                self.printer.modelo = linha.strip()



            elif "serial" in l:

                self.printer.serial = linha.strip()



            elif "manufacturer" in l:

                self.printer.fabricante = linha.strip()