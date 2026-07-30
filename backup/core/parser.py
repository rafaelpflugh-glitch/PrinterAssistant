import re


class PrinterParser:

    def __init__(self, texto):

        self.texto = texto

        self.info = {
            "fabricante": None,
            "modelo": None,
            "serial": None,
            "firmware": None
        }

    def parse(self):

        self.fabricante()

        self.modelo()

        self.serial()

        self.firmware()

        return self.info

    def fabricante(self):

        if "lexmark" in self.texto.lower():

            self.info["fabricante"] = "Lexmark"

    def modelo(self):

        padroes = [

            r"\bMX\d{3}\b",

            r"\bCX\d{3}\b",

            r"\bMS\d{3}\b",

            r"\bCS\d{3}\b"

        ]

        for p in padroes:

            achou = re.search(
                p,
                self.texto,
                re.I
            )

            if achou:

                self.info["modelo"] = achou.group().upper()

                return

    def serial(self):

        padroes = [

            r"Serial Number:\s*([A-Z0-9]+)",

            r"serialNumber.*?([A-Z0-9]{8,20})"

        ]

        for p in padroes:

            achou = re.search(
                p,
                self.texto,
                re.I
            )

            if achou:

                self.info["serial"] = achou.group(1)

                return

    def firmware(self):

        linhas = self.texto.splitlines()

        for i, linha in enumerate(linhas):

            if "Firmware Version" in linha:

                if i + 1 < len(linhas):

                    self.info["firmware"] = linhas[i + 1].strip()

                    return