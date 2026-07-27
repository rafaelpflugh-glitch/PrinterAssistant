import json


class Database:

    def __init__(self):

        with open(
            "database/commands.json",
            encoding="utf-8"
        ) as arq:

            self.db = json.load(arq)


    def comando(self, nome):

        return self.db.get(nome)


database = Database()