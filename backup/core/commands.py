import json

from core.executor import Executor


class Commands:

    def __init__(self, printer):

        self.executor = Executor(printer)

        with open(
            "database/commands.json",
            encoding="utf-8"
        ) as f:

            self.db = json.load(f)

    def executar(self, nome):

        if nome not in self.db:

            print("Comando inexistente.")

            return

        cmd = self.db[nome]

        metodo = cmd["method"]

        endpoint = cmd["endpoint"]

        if metodo == "GET":

            return self.executor.get(endpoint)

        elif metodo == "POST":

            return self.executor.post(endpoint)