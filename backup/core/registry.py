import os
import importlib


class Registry:

    def __init__(self):

        self.comandos = {}


    def carregar(self):

        pasta = "commands"

        for arquivo in os.listdir(pasta):

            if not arquivo.endswith(".py"):
                continue

            if arquivo.startswith("_"):
                continue

            nome = arquivo[:-3]

            modulo = importlib.import_module(
                f"commands.{nome}"
            )

            if hasattr(modulo, "INFO"):

                self.comandos[
                    modulo.INFO["id"]
                ] = modulo


registry = Registry()