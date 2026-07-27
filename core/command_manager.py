import json
import os



class CommandManager:


    def __init__(self):

        self.arquivo = os.path.join(
            "data",
            "commands.json"
        )



    def carregar(self):

        if not os.path.exists(self.arquivo):

            return {}

        with open(
            self.arquivo,
            encoding="utf-8"
        ) as f:

            return json.load(f)




    def listar(self, marca):


        comandos = self.carregar()


        for fabricante, lista in comandos.items():

            if fabricante.lower() == marca.lower():

                return lista



        return []