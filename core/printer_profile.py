import os
import json
from datetime import datetime



class PrinterProfile:


    def __init__(self, ip):

        self.ip = ip

        self.pasta = os.path.join(

            "data",

            "printers",

            ip

        )


        os.makedirs(

            self.pasta,

            exist_ok=True

        )


        self.arquivo = os.path.join(

            self.pasta,

            "perfil.json"

        )




    def salvar(self, dados):


        dados["ultima_atualizacao"] = (

            datetime.now().strftime(

                "%d/%m/%Y %H:%M"

            )

        )


        with open(

            self.arquivo,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                dados,

                f,

                indent=4,

                ensure_ascii=False

            )


        return self.arquivo





    def carregar(self):


        if not os.path.exists(

            self.arquivo

        ):

            return None



        with open(

            self.arquivo,

            encoding="utf-8"

        ) as f:


            return json.load(f)