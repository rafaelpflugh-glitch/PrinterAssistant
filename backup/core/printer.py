import requests

from tools.debug import coletar_debug

from core.parser import PrinterParser


class Printer:

    def __init__(self, ip):

        self.ip = ip

        self.hostname = ip

        self.fabricante = None

        self.modelo = None

        self.serial = None

        self.firmware = None

        self.debug = None

        self.identificar()

    def identificar(self):

        try:

            self.debug = coletar_debug(self.ip)

            if not self.debug:

                return

            parser = PrinterParser(self.debug)

            dados = parser.parse()

            self.fabricante = dados["fabricante"]

            self.modelo = dados["modelo"]

            self.serial = dados["serial"]

            self.firmware = dados["firmware"]

        except Exception as erro:

            print(erro)