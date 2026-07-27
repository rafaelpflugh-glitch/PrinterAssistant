import asyncio


# ============================================================
# PRINTER ASSISTANT - DEVICE
# ============================================================
#
# Representa uma impressora física dentro do sistema.
#
# Este módulo NÃO faz a comunicação diretamente.
#
# Ele utiliza:
#
#   core.pjl  -> identificação / contador
#   core.snmp -> suprimentos
#
# Objetivo:
#
# Transformar uma impressora em um objeto único:
#
#   PrinterDevice
#
# No futuro será esse objeto que o scanner entregará
# para o restante do sistema.
#
# ============================================================


from core.pjl import coletar_identificacao
from core.snmp import coletar_supplies


# ============================================================
# CLASSE DA IMPRESSORA
# ============================================================

class PrinterDevice:

    def __init__(
        self,
        ip,
        nome=None
    ):

        self.ip = ip

        self.nome = nome

        self.identificacao = {

            "fabricante": "Desconhecido",

            "modelo": "Desconhecido",

            "familia": "",

            "tipo": "",

            "serial": "Desconhecido",

            "contador": None

        }

        self.supplies = []

        self.conectividade = {

            "ip": ip,

            "snmp": False,

            "pjl": False,

            "web": False,

            "raw": False,

            "ipp": False

        }


    # ========================================================
    # FABRICANTE
    # ========================================================

    def detectar_fabricante(
        self,
        modelo
    ):

        texto = str(
            modelo or ""
        ).lower()


        if "lexmark" in texto:

            return "Lexmark"


        if "brother" in texto:

            return "Brother"


        if "canon" in texto:

            return "Canon"


        if (
            "hp" in texto
            or
            "hewlett" in texto
        ):

            return "HP"


        return "Desconhecido"


    # ========================================================
    # FAMÍLIA
    # ========================================================

    def detectar_familia(
        self,
        modelo
    ):

        if not modelo:

            return ""


        partes = str(
            modelo
        ).split()


        if not partes:

            return ""


        # ----------------------------------------------------
        # Lexmark normalmente aparece como:
        #
        # Lexmark MX611dhe
        #
        # Queremos:
        #
        # MX
        # ----------------------------------------------------

        if (
            partes[0].lower()
            == "lexmark"
            and
            len(partes) > 1
        ):

            modelo_texto = partes[1].upper()


        else:

            modelo_texto = partes[0].upper()


        if modelo_texto.startswith(
            "MX"
        ):

            return "MX"


        if modelo_texto.startswith(
            "MS"
        ):

            return "MS"


        if modelo_texto.startswith(
            "CX"
        ):

            return "CX"


        if modelo_texto.startswith(
            "CS"
        ):

            return "CS"


        if modelo_texto.startswith(
            "XM"
        ):

            return "XM"


        return modelo_texto


    # ========================================================
    # TIPO DO EQUIPAMENTO
    # ========================================================

    def detectar_tipo(
        self,
        fabricante,
        modelo
    ):

        modelo_lower = str(
            modelo or ""
        ).lower()


        if fabricante == "Lexmark":

            if "mx" in modelo_lower:

                return (
                    "Multifuncional Laser Mono"
                )


            if "ms" in modelo_lower:

                return (
                    "Impressora Laser Mono"
                )


            if "cx" in modelo_lower:

                return (
                    "Multifuncional Laser Color"
                )


            if "cs" in modelo_lower:

                return (
                    "Impressora Laser Color"
                )


            return "Impressora Lexmark"


        if fabricante == "Brother":

            return "Impressora Brother"


        if fabricante == "Canon":

            return "Impressora Canon"


        if fabricante == "HP":

            return "Impressora HP"


        return "Equipamento de impressão"


    # ========================================================
    # NORMALIZAR IDENTIFICAÇÃO
    # ========================================================

    def normalizar_identificacao(
        self,
        dados
    ):

        if not dados:

            return


        modelo = dados.get(
            "modelo"
        )


        serial = dados.get(
            "serial"
        )


        contador = dados.get(
            "contador"
        )


        if not modelo:

            modelo = "Desconhecido"


        if not serial:

            serial = "Desconhecido"


        fabricante = (
            self.detectar_fabricante(
                modelo
            )
        )


        familia = (
            self.detectar_familia(
                modelo
            )
        )


        tipo = (
            self.detectar_tipo(
                fabricante,
                modelo
            )
        )


        self.identificacao = {

            "fabricante":
                fabricante,

            "modelo":
                modelo,

            "familia":
                familia,

            "tipo":
                tipo,

            "serial":
                serial,

            "contador":
                contador

        }


    # ========================================================
    # COLETAR PJL
    # ========================================================

    def coletar_pjl(
        self
    ):

        try:

            dados = (
                coletar_identificacao(
                    self.ip
                )
            )


            if dados:

                self.normalizar_identificacao(
                    dados
                )


                self.conectividade[
                    "pjl"
                ] = bool(
                    dados.get("modelo")
                    or
                    dados.get("serial")
                    or
                    dados.get("contador")
                )


                self.conectividade[
                    "raw"
                ] = self.conectividade[
                    "pjl"
                ]


                return dados


        except Exception as erro:

            print(
                f"[DEVICE] Erro PJL: {erro}"
            )


        return {}


    # ========================================================
    # COLETAR SNMP
    # ========================================================

    async def coletar_snmp(
        self
    ):

        try:

            dados = await coletar_supplies(
                self.ip
            )


            if dados is not None:

                self.supplies = dados


                self.conectividade[
                    "snmp"
                ] = True


                return dados


        except Exception as erro:

            print(
                f"[DEVICE] Erro SNMP: {erro}"
            )


        self.supplies = []


        return []


    # ========================================================
    # COLETA COMPLETA
    # ========================================================

    async def coletar(
        self
    ):

        # ----------------------------------------------------
        # PJL é síncrono
        # ----------------------------------------------------

        self.coletar_pjl()


        # ----------------------------------------------------
        # SNMP é assíncrono
        # ----------------------------------------------------

        await self.coletar_snmp()


        return self.to_dict()


    # ========================================================
    # ESTADO GERAL
    # ========================================================

    def estado(
        self
    ):

        if (
            self.conectividade["pjl"]
            and
            self.conectividade["snmp"]
        ):

            return "EXCELENTE"


        if (
            self.conectividade["pjl"]
            or
            self.conectividade["snmp"]
        ):

            return "PARCIAL"


        return "OFFLINE"


    # ========================================================
    # TOTAL DE SUPRIMENTOS
    # ========================================================

    def total_supplies(
        self
    ):

        return len(
            self.supplies
        )


    # ========================================================
    # CONTADOR
    # ========================================================

    def contador(
        self
    ):

        return self.identificacao.get(
            "contador"
        )


    # ========================================================
    # SERIAL
    # ========================================================

    def serial(
        self
    ):

        return self.identificacao.get(
            "serial"
        )


    # ========================================================
    # MODELO
    # ========================================================

    def modelo(
        self
    ):

        return self.identificacao.get(
            "modelo"
        )


    # ========================================================
    # REPRESENTAÇÃO
    # ========================================================

    def to_dict(
        self
    ):

        return {

            "ip":
                self.ip,

            "nome":
                self.nome,

            "identificacao":
                self.identificacao,

            "conectividade":
                self.conectividade,

            "supplies":
                self.supplies,

            "estado":
                self.estado(),

            "total_supplies":
                self.total_supplies()

        }


# ============================================================
# FUNÇÃO DE CONVENIÊNCIA
# ============================================================

async def coletar_device(
    ip,
    nome=None
):

    device = PrinterDevice(

        ip=ip,

        nome=nome

    )


    await device.coletar()


    return device


# ============================================================
# TESTE DIRETO
# ============================================================

async def teste():

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE DEVICE"
    )

    print("=" * 60)


    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()


    if not ip:

        print(
            "IP não informado."
        )

        return


    print()

    print(
        "Criando dispositivo..."
    )


    device = PrinterDevice(
        ip
    )


    print()

    print(
        "Coletando dados..."
    )


    await device.coletar()


    print()

    print("=" * 60)

    print(
        "DISPOSITIVO"
    )

    print("=" * 60)


    print()

    print(
        "IP:",
        device.ip
    )


    print(
        "Fabricante:",
        device.identificacao[
            "fabricante"
        ]
    )


    print(
        "Modelo:",
        device.identificacao[
            "modelo"
        ]
    )


    print(
        "Família:",
        device.identificacao[
            "familia"
        ]
    )


    print(
        "Tipo:",
        device.identificacao[
            "tipo"
        ]
    )


    print(
        "Serial:",
        device.identificacao[
            "serial"
        ]
    )


    print(
        "Contador:",
        device.identificacao[
            "contador"
        ]
    )


    print()

    print(
        "PJL:",
        "ATIVO"
        if device.conectividade[
            "pjl"
        ]
        else
        "INATIVO"
    )


    print(
        "SNMP:",
        "ATIVO"
        if device.conectividade[
            "snmp"
        ]
        else
        "INATIVO"
    )


    print(
        "Estado:",
        device.estado()
    )


    print(
        "Suprimentos:",
        device.total_supplies()
    )


    print()

    print("=" * 60)

    print(
        "SUPRIMENTOS"
    )

    print("=" * 60)


    for numero, supply in enumerate(

        device.supplies,

        start=1

    ):

        print()

        print(
            f"[{numero}]",
            supply.get(
                "nome",
                "Desconhecido"
            )
        )


        print(
            "    Nível:",
            f'{supply.get("nivel", 0)}%'
        )


        print(
            "    Status:",
            supply.get(
                "status",
                "DESCONHECIDO"
            )
        )


    print()

    print("=" * 60)

    print(
        "TESTE CONCLUÍDO"
    )

    print("=" * 60)


    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        teste()
    )