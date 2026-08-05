from core.intent.intent import Intent


class IntentResolver:

    def __init__(self):

        self.commands = {

            "pagecount": ("pjl", "pagecount"),
            "contador": ("pjl", "pagecount"),
            "quantas paginas": ("pjl", "pagecount"),

            "status": ("pjl", "status"),
            "estado": ("pjl", "status"),

            "memoria": ("pjl", "memory"),

            "serial": ("pjl", "id"),

            "modelo": ("pjl", "prodinfo"),
            "produto": ("pjl", "prodinfo"),

            "config": ("pjl", "config"),
            "variaveis": ("pjl", "variables"),

            "reset": ("reset", "cold"),
            "cold reset": ("reset", "cold"),

            "firmware": ("firmware", "version")

        }

    # ------------------------------------------------------

    def resolve(self, text):

        texto = text.lower()

        for alias, (tool, action) in self.commands.items():

            if alias in texto:

                return Intent(

                    tool=tool,

                    action=action,

                    confidence=1.0,

                    arguments={},

                    text=text

                )

        return None