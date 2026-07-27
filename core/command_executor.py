import requests
import json
import os

from core.printer_memory import PrinterMemory
from core.safety import Safety



class CommandExecutor:


    def __init__(self, ip):

        self.ip = ip

        self.base = f"http://{ip}"

        self.memoria = PrinterMemory(ip)

        self.session = requests.Session()


        self.session.headers.update({

            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",

            "Accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

        })


        self.login()




    def login(self):

        try:

            resposta = self.session.get(
                self.base,
                timeout=10
            )


            print(
                "Sessão EWS:",
                resposta.status_code
            )


        except Exception as erro:


            print(
                "Erro sessão:",
                erro
            )




    def carregar_comandos(self):


        caminho = os.path.join(
            "data",
            "commands.json"
        )


        if not os.path.exists(caminho):

            print(
                "Banco de comandos não encontrado:",
                caminho
            )

            return {}



        with open(
            caminho,
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)





    def salvar_exportacao(self, conteudo):


        caminho = self.memoria.caminho_config()


        with open(
            caminho,
            "wb"
        ) as arquivo:

            arquivo.write(conteudo)


        return caminho





    def executar(self, marca, comando):


        comandos = self.carregar_comandos()


        lista = []



        for fabricante, itens in comandos.items():


            if fabricante.lower() == marca.lower():

                lista = itens

                break





        alvo = None



        for item in lista:


            if item["nome"].lower() == comando.lower():

                alvo = item

                break




        if not alvo:


            return {

                "erro":
                "comando não encontrado",

                "disponiveis":
                [
                    x["nome"]
                    for x in lista
                ]

            }





        if not Safety.confirmar(alvo):

            return {

                "cancelado":
                True

            }




        url = self.base + alvo["endpoint"]




        print()

        print("=================================")

        print("EXECUTANDO")

        print(alvo["nome"])

        print(url)

        print("=================================")




        try:


            headers = {


                "Referer":
                self.base,


                "Content-Type":
                "application/x-www-form-urlencoded",


                "Origin":
                self.base

            }





            metodo = alvo.get(
                "metodo",
                "POST"
            ).upper()





            if metodo == "POST":


                resposta = self.session.post(

                    url,

                    data=alvo.get(
                        "dados",
                        {}
                    ),

                    headers=headers,

                    allow_redirects=True,

                    timeout=20

                )


            else:


                resposta = self.session.get(

                    url,

                    headers=headers,

                    timeout=20

                )






            content_type = resposta.headers.get(
                "Content-Type",
                ""
            )



            arquivo_salvo = None





            if (

                "download" in content_type.lower()

                or

                "octet-stream" in content_type.lower()

            ):


                arquivo_salvo = self.salvar_exportacao(
                    resposta.content
                )


                print()

                print(
                    "Configuração salva:",
                    arquivo_salvo
                )






            return {


                "status":
                resposta.status_code,


                "tamanho":
                len(resposta.content),


                "content_type":
                content_type,


                "arquivo":
                arquivo_salvo,


                "resposta":
                resposta.text[:500]

                if "text" in content_type.lower()

                else ""

            }




        except Exception as erro:


            return {

                "erro":
                str(erro)

            }