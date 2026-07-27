import os
import json



class PrinterMemory:


    def __init__(self, ip):

        self.ip = ip

        self.path = os.path.join(

            "data",

            "printers",

            ip

        )



        os.makedirs(

            self.path,

            exist_ok=True

        )





    def salvar_info(self, dados):


        arquivo = os.path.join(

            self.path,

            "info.json"

        )


        with open(

            arquivo,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                dados,

                f,

                indent=4,

                ensure_ascii=False

            )



        return arquivo





    def caminho_config(self):


        return os.path.join(

            self.path,

            "config.ucf"

        )