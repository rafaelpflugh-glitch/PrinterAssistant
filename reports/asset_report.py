import json
from datetime import datetime


class AssetReport:


    def __init__(self, device, session=None):

        self.device = device
        self.session = session



    def gerar(self):

        dados = self.device.to_dict()


        ident = dados.get(
            "identificacao",
            {}
        )


        conexao = dados.get(
            "conectividade",
            {}
        )


        relatorio = {


            "data":

                datetime.now()
                .strftime("%d/%m/%Y %H:%M"),



            "equipamento": {


                "fabricante":
                    ident.get(
                        "fabricante"
                    ),


                "modelo":
                    ident.get(
                        "modelo"
                    ),


                "familia":
                    ident.get(
                        "familia"
                    ),


                "tipo":
                    ident.get(
                        "tipo"
                    ),


                "serial":
                    ident.get(
                        "serial"
                    ),


                "contador":
                    ident.get(
                        "contador"
                    )

            },


            "rede": conexao,


            "suprimentos":
                dados.get(
                    "supplies",
                    []
                ),



            "estado":
                dados.get(
                    "estado"
                )

        }


        return relatorio




    def salvar_json(self):


        relatorio = self.gerar()



        nome = (

            "reports/"
            +
            relatorio["equipamento"]["fabricante"]
            +
            "_"
            +
            relatorio["equipamento"]["modelo"]
            +
            ".json"

        )


        with open(

            nome,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                relatorio,

                f,

                indent=4,

                ensure_ascii=False

            )


        return nome