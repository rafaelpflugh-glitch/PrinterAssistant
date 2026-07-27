# ============================================================
# PRINTER ASSISTANT
# core/device.py
#
# Modelo e identificação dos dispositivos encontrados na rede.
# ============================================================

import json
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ARQUIVO_DISPOSITIVOS = (
    Path(__file__).resolve().parent.parent
    / "printers_found.json"
)


# ============================================================
# CLASSE DO DISPOSITIVO
# ============================================================

class PrinterDevice:

    def __init__(self, dados):

        # ----------------------------------------------------
        # IDENTIFICAÇÃO BÁSICA
        # ----------------------------------------------------

        self.ip = dados.get("ip")

        self.fabricante = "Desconhecido"
        self.modelo = "Desconhecido"
        self.familia = ""
        self.tipo = ""

        # ----------------------------------------------------
        # SERVIÇOS DETECTADOS
        # ----------------------------------------------------

        self.web = bool(
            dados.get("web", False)
        )

        self.raw = bool(
            dados.get("raw", False)
        )

        self.ipp = bool(
            dados.get("ipp", False)
        )

        self.snmp_resposta = dados.get(
            "snmp"
        )

        self.suporta_snmp = bool(
            self.snmp_resposta
        )

        # ----------------------------------------------------
        # CAPACIDADES
        # ----------------------------------------------------

        self.suporta_pjl = False

        # ----------------------------------------------------
        # IDENTIFICAÇÃO
        # ----------------------------------------------------

        self.identificar()

        # ----------------------------------------------------
        # INTEGRAÇÃO
        # ----------------------------------------------------

        self.integracao = self.calcular_integracao()


    # ========================================================
    # IDENTIFICAÇÃO PRINCIPAL
    # ========================================================

    def identificar(self):

        if not self.snmp_resposta:
            return

        texto = self.snmp_resposta.lower()

        # ----------------------------------------------------
        # LEXMARK
        # ----------------------------------------------------

        if "lexmark" in texto:

            self.fabricante = "Lexmark"

            self.identificar_lexmark(
                texto
            )

            # Atualmente nosso módulo PJL
            # é direcionado para Lexmark.
            self.suporta_pjl = True

            return


        # ----------------------------------------------------
        # BROTHER
        # ----------------------------------------------------

        if "brother" in texto:

            self.fabricante = "Brother"

            self.identificar_brother(
                texto
            )

            return


        # ----------------------------------------------------
        # HP
        # ----------------------------------------------------

        if (
            "hewlett" in texto
            or "hp " in texto
            or texto.startswith("hp")
        ):

            self.fabricante = "HP"

            self.tipo = "Impressora HP"

            return


        # ----------------------------------------------------
        # CANON
        # ----------------------------------------------------

        if "canon" in texto:

            self.fabricante = "Canon"

            self.tipo = "Impressora Canon"

            return


        # ----------------------------------------------------
        # OUTRO DISPOSITIVO SNMP
        # ----------------------------------------------------

        self.fabricante = "Desconhecido"


    # ========================================================
    # IDENTIFICAÇÃO LEXMARK
    # ========================================================

    def identificar_lexmark(self, texto):

        modelos = {

            "mx611": (
                "MX611",
                "MX",
                "Multifuncional Laser Mono"
            ),

            "mx511": (
                "MX511",
                "MX",
                "Multifuncional Laser Mono"
            ),

            "mx711": (
                "MX711",
                "MX",
                "Multifuncional Laser Mono"
            ),

            "ms610": (
                "MS610",
                "MS",
                "Laser Mono"
            ),

            "e460": (
                "E460",
                "E",
                "Laser Mono"
            ),

            "cs725": (
                "CS725",
                "CS",
                "Laser Color"
            ),

            "cx510": (
                "CX510",
                "CX",
                "Laser Color MFP"
            ),

        }


        for chave, dados in modelos.items():

            if chave in texto:

                (
                    self.modelo,
                    self.familia,
                    self.tipo
                ) = dados

                return


        # Lexmark identificada,
        # mas modelo ainda não conhecido.

        self.modelo = "Lexmark"
        self.familia = "Desconhecida"
        self.tipo = "Impressora Lexmark"


    # ========================================================
    # IDENTIFICAÇÃO BROTHER
    # ========================================================

    def identificar_brother(self, texto):

        # Alguns modelos Brother podem aparecer
        # apenas pelo nome da placa/controladora.
        #
        # O modelo real será refinado posteriormente
        # através de SNMP/PJL/Web.

        self.modelo = "Desconhecido"
        self.familia = ""
        self.tipo = "Impressora Brother"


    # ========================================================
    # CÁLCULO DE INTEGRAÇÃO
    # ========================================================

    def calcular_integracao(self):

        pontos = 0

        # ----------------------------------------------------
        # WEB
        # ----------------------------------------------------

        if self.web:
            pontos += 20


        # ----------------------------------------------------
        # RAW / PORTA 9100
        # ----------------------------------------------------

        if self.raw:
            pontos += 20


        # ----------------------------------------------------
        # IPP
        # ----------------------------------------------------

        if self.ipp:
            pontos += 20


        # ----------------------------------------------------
        # SNMP
        # ----------------------------------------------------

        if self.suporta_snmp:
            pontos += 20


        # ----------------------------------------------------
        # PJL
        # ----------------------------------------------------

        if self.suporta_pjl:
            pontos += 20


        return pontos


    # ========================================================
    # NÍVEL DE INTEGRAÇÃO
    # ========================================================

    def nivel_integracao(self):

        if self.integracao >= 80:
            return "ALTA"

        if self.integracao >= 40:
            return "MEDIA"

        if self.integracao >= 20:
            return "BAIXA"

        return "MINIMA"


    # ========================================================
    # RESUMO
    # ========================================================

    def resumo(self):

        return {

            "ip":
                self.ip,

            "fabricante":
                self.fabricante,

            "modelo":
                self.modelo,

            "familia":
                self.familia,

            "tipo":
                self.tipo,

            "web":
                self.web,

            "raw":
                self.raw,

            "ipp":
                self.ipp,

            "snmp":
                self.suporta_snmp,

            "pjl":
                self.suporta_pjl,

            "integracao":
                self.integracao,

            "nivel_integracao":
                self.nivel_integracao()

        }


# ============================================================
# CARREGAR DISPOSITIVOS
# ============================================================

def carregar_dispositivos(
    caminho=None
):

    if caminho is None:

        caminho = (
            ARQUIVO_DISPOSITIVOS
        )


    caminho = Path(
        caminho
    )


    if not caminho.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )


    with caminho.open(
        "r",
        encoding="utf-8"
    ) as arq:

        bruto = json.load(
            arq
        )


    dispositivos = []


    for dados in bruto:

        dispositivos.append(
            PrinterDevice(dados)
        )


    return dispositivos


# ============================================================
# BUSCAR DISPOSITIVO POR IP
# ============================================================

def buscar_por_ip(
    ip,
    dispositivos=None
):

    if dispositivos is None:

        dispositivos = (
            carregar_dispositivos()
        )


    for dispositivo in dispositivos:

        if dispositivo.ip == ip:

            return dispositivo


    return None


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    dispositivos = (
        carregar_dispositivos()
    )


    print()
    print("=" * 70)
    print(
        "DISPOSITIVOS IDENTIFICADOS"
    )
    print("=" * 70)


    for dispositivo in dispositivos:

        resumo = dispositivo.resumo()


        print()

        print(
            f"IP             : "
            f"{resumo['ip']}"
        )

        print(
            f"Fabricante     : "
            f"{resumo['fabricante']}"
        )

        print(
            f"Modelo         : "
            f"{resumo['modelo']}"
        )

        print(
            f"Família        : "
            f"{resumo['familia']}"
        )

        print(
            f"Tipo           : "
            f"{resumo['tipo']}"
        )

        print(
            f"WEB            : "
            f"{resumo['web']}"
        )

        print(
            f"RAW 9100       : "
            f"{resumo['raw']}"
        )

        print(
            f"IPP            : "
            f"{resumo['ipp']}"
        )

        print(
            f"SNMP           : "
            f"{resumo['snmp']}"
        )

        print(
            f"PJL            : "
            f"{resumo['pjl']}"
        )

        print(
            f"Integração     : "
            f"{resumo['integracao']}%"
        )

        print(
            f"Nível          : "
            f"{resumo['nivel_integracao']}"
        )


    print()
    print(
        f"Total: {len(dispositivos)}"
    )
    print()