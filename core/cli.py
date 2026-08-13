"""
============================================================
Printer Assistant
CLI
============================================================
"""

from core.session import Session
from core.tool_manager import ToolManager
from core.intent.intent_resolver import IntentResolver


class CLI:

    def __init__(self):

        self.session = Session()

        self.tools = ToolManager(self.session)

        self.resolver = IntentResolver()

    # =====================================================

    def banner(self):

        print()

        print("=" * 60)

        print("PRINTER ASSISTANT")

        print("=" * 60)

        print()

        print("Comandos disponíveis:")

        print()

        print("connect <ip>")

        print("contador")

        print("modelo")

        print("status")

        print("memoria")

        print("help")

        print("exit")

        print()

    # =====================================================

    def execute(self, text):

        partes = text.split()

        if not partes:

            return

        comando = partes[0].lower()

        #
        # conexão
        #

        if comando == "connect":

            if len(partes) < 2:

                print("Informe o IP.")

                return

            ip = partes[1]

            self.session.connect(ip)

            print()

            print(f"Impressora conectada em {ip}")

            print()

            return

        #
        # ajuda
        #

        if comando == "help":

            self.banner()

            return

        #
        # intents
        #

        intent = self.resolver.resolve(text)

        if intent is None:

            print()

            print("Comando desconhecido.")

            print()

            return

        resultado = self.tools.execute(

            intent.tool,

            intent.action,

            **(intent.arguments or {})

        )

        print()

        print(resultado)

        print()