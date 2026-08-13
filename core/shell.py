"""
============================================================
Printer Assistant
Shell principal
============================================================
"""

from core.cli import CLI


class Shell:

    def __init__(self):

        self.cli = CLI()

    def run(self):

        self.cli.banner()

        while True:

            try:

                comando = input("> ").strip()

            except KeyboardInterrupt:

                print()

                break

            except EOFError:

                print()

                break

            if not comando:

                continue

            if comando.lower() in ("exit", "quit", "sair"):

                print()

                print("Encerrando Printer Assistant...")

                break

            self.cli.execute(comando)