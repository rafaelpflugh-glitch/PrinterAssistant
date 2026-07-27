import json


class PrinterDevice:

    def __init__(self, dados):

        self.ip = dados.get("ip")

        self.web = dados.get("web", False)

        self.raw = dados.get("raw", False)

        self.ipp = dados.get("ipp", False)

        self.snmp = dados.get("snmp")

        self.fabricante = "Desconhecido"

        self.modelo = "Desconhecido"

        self.familia = ""

        self.tipo = ""

        self.suporta_pjl = False

        self.suporta_snmp = False

        self.suporta_raw = self.raw

        self.nivel_integracao = 0

        self.identificar()


    def identificar(self):

        if not self.snmp:

            return

        texto = self.snmp.lower()

        self.suporta_snmp = True

        if "lexmark" in texto:

            self.fabricante = "Lexmark"

            self.suporta_pjl = True

            self.nivel_integracao = 100

            self.identificar_lexmark(texto)

        elif "brother" in texto:

            self.fabricante = "Brother"

            self.nivel_integracao = 40

        elif "hp" in texto or "hewlett" in texto:

            self.fabricante = "HP"

            self.nivel_integracao = 50

        elif "canon" in texto:

            self.fabricante = "Canon"

            self.nivel_integracao = 40


    def identificar_lexmark(self, texto):

        if "mx611" in texto:

            self.modelo = "MX611dhe"

            self.familia = "MX"

            self.tipo = "Multifuncional Laser Mono"

        elif "mx511" in texto:

            self.modelo = "MX511"

            self.familia = "MX"

            self.tipo = "Multifuncional Laser Mono"

        elif "mx711" in texto:

            self.modelo = "MX711"

            self.familia = "MX"

            self.tipo = "Multifuncional Laser Mono"

        elif "ms610" in texto:

            self.modelo = "MS610"

            self.familia = "MS"

            self.tipo = "Laser Mono"

        elif "e460" in texto:

            self.modelo = "E460"

            self.familia = "E"

            self.tipo = "Laser Mono"

        elif "cs725" in texto:

            self.modelo = "CS725"

            self.familia = "CS"

            self.tipo = "Laser Color"

        elif "cx510" in texto:

            self.modelo = "CX510"

            self.familia = "CX"

            self.tipo = "Laser Color MFP"

        else:

            self.modelo = "Lexmark"

            self.familia = "Desconhecida"


    def resumo(self):

        return {

            "ip": self.ip,

            "fabricante": self.fabricante,

            "modelo": self.modelo,

            "familia": self.familia,

            "tipo": self.tipo,

            "web": self.web,

            "raw": self.raw,

            "ipp": self.ipp,

            "snmp": self.suporta_snmp,

            "pjl": self.suporta_pjl,

            "integracao": self.nivel_integracao

        }


def carregar_dispositivos():

    with open(

        "printers_found.json",

        encoding="utf-8"

    ) as arq:

        bruto = json.load(arq)

    lista = []

    for d in bruto:

        lista.append(

            PrinterDevice(d)

        )

    return lista