from core.intent.intent import Intent


class IntentResolver:

    def __init__(self):

        self.commands = {

            "pagecount":

            Intent(

                tool="pjl",

                action="pagecount"

            ),

            "contador":

            Intent(

                tool="pjl",

                action="pagecount"

            ),

            "quantas paginas":

            Intent(

                tool="pjl",

                action="pagecount"

            ),

            "status":

            Intent(

                tool="pjl",

                action="status"

            ),

            "estado":

            Intent(

                tool="pjl",

                action="status"

            ),

            "memoria":

            Intent(

                tool="pjl",

                action="memory"

            ),

            "serial":

            Intent(

                tool="pjl",

                action="id"

            ),

            "modelo":

            Intent(

                tool="pjl",

                action="prodinfo"

            ),

            "produto":

            Intent(

                tool="pjl",

                action="prodinfo"

            )

        }

    # ------------------------------------------

    def resolve(self, text):

        text = text.lower()

        for alias, intent in self.commands.items():

            if alias in text:

                return intent

        return None