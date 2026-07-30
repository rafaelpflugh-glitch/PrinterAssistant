import asyncio

from core.pjl import coletar_identificacao
from core.snmp import coletar_supplies


# ============================================================
# PRINTER ASSISTANT - DEVICE
# ============================================================
#
# Representa uma impressora física dentro do sistema.
#
# PJL  -> identificação / contador
# SNMP -> suprimentos
#
# IMPORTANTE:
#
# O Device não implementa SNMP.
# O Device não implementa PJL.
#
# Apenas coordena os coletores existentes.
#
# ============================================================


TIMEOUT_PJL = 15

# Limite de segurança.
#
# O core.snmp possui seu próprio controle de timeout.
# Este limite não deve ser pequeno.
#
TIMEOUT_SNMP = 45


# ============================================================
# CLASSE
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

            "fabricante":
                "Desconhecido",

            "modelo":
                "Desconhecido",

            "familia":
                "",

            "tipo":
                "",

            "serial":
                "Desconhecido",

            "contador":
                None

        }

        self.supplies = []

        self.conectividade = {

            "ip":
                ip,

            "snmp":
                False,

            "pjl":
                False,

            "web":
                False,

            "raw":
                False,

            "ipp":
                False

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

        if (
            partes[0].lower() == "lexmark"
            and
            len(partes) > 1
        ):

            modelo_texto = (
                partes[1].upper()
            )

        else:

            modelo_texto = (
                partes[0].upper()
            )

        familias = (
            "MX",
            "MS",
            "CX",
            "CS",
            "XM"
        )

        for familia in familias:

            if modelo_texto.startswith(
                familia
            ):

                return familia

        return modelo_texto


    # ========================================================
    # TIPO
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
                return "Multifuncional Laser Mono"

            if "ms" in modelo_lower:
                return "Impressora Laser Mono"

            if "cx" in modelo_lower:
                return "Multifuncional Laser Color"

            if "cs" in modelo_lower:
                return "Impressora Laser Color"

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

        modelo_novo = dados.get(
            "modelo"
        )

        serial_novo = dados.get(
            "serial"
        )

        contador_novo = dados.get(
            "contador"
        )

        modelo_atual = (
            self.identificacao.get(
                "modelo"
            )
        )

        serial_atual = (
            self.identificacao.get(
                "serial"
            )
        )

        contador_atual = (
            self.identificacao.get(
                "contador"
            )
        )

        if (
            not modelo_novo
            and
            modelo_atual
            and
            modelo_atual != "Desconhecido"
        ):

            modelo_novo = modelo_atual

        if not modelo_novo:
            modelo_novo = "Desconhecido"

        if (
            not serial_novo
            and
            serial_atual
            and
            serial_atual != "Desconhecido"
        ):

            serial_novo = serial_atual

        if not serial_novo:
            serial_novo = "Desconhecido"

        if contador_novo is None:

            contador_novo = (
                contador_atual
            )

        fabricante = (
            self.detectar_fabricante(
                modelo_novo
            )
        )

        familia = (
            self.detectar_familia(
                modelo_novo
            )
        )

        tipo = (
            self.detectar_tipo(
                fabricante,
                modelo_novo
            )
        )

        self.identificacao = {

            "fabricante":
                fabricante,

            "modelo":
                modelo_novo,

            "familia":
                familia,

            "tipo":
                tipo,

            "serial":
                serial_novo,

            "contador":
                contador_novo

        }


    # ========================================================
    # PJL
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

            if not dados:
                return {}

            self.normalizar_identificacao(
                dados
            )

            respondeu = bool(

                dados.get("modelo")
                or
                dados.get("serial")
                or
                dados.get("contador")

            )

            if respondeu:

                self.conectividade[
                    "pjl"
                ] = True

                self.conectividade[
                    "raw"
                ] = True

            return dados

        except Exception as erro:

            print(
                f"[DEVICE] Erro PJL: {erro}"
            )

            return {}


    # ========================================================
    # SNMP
    # ========================================================

    async def coletar_snmp(
        self
    ):

        print(
            "[DEVICE] Consultando suprimentos via SNMP..."
        )

        try:

            dados = await asyncio.wait_for(

                coletar_supplies(
                    self.ip
                ),

                timeout=TIMEOUT_SNMP

            )

        except asyncio.TimeoutError:

            print(
                "[DEVICE] SNMP excedeu o limite externo "
                f"de {TIMEOUT_SNMP} segundos."
            )

            return self.supplies

        except Exception as erro:

            print(
                f"[DEVICE] Erro SNMP: {erro}"
            )

            return self.supplies


        if dados is None:

            print(
                "[DEVICE] SNMP não retornou dados."
            )

            return self.supplies


        if not dados:

            print(
                "[DEVICE] SNMP respondeu, "
                "mas não encontrou suprimentos."
            )

            return self.supplies


        self.supplies = list(
            dados
        )

        self.conectividade[
            "snmp"
        ] = True

        print(
            "[DEVICE] SNMP encontrou "
            f"{len(self.supplies)} suprimentos."
        )

        return self.supplies


    # ========================================================
    # COLETA COMPLETA
    # ========================================================

    async def coletar(
        self
    ):

        # ----------------------------------------------------
        # PRIMEIRO: PJL
        #
        # Mantemos a identificação previsível.
        # ----------------------------------------------------

        try:

            await asyncio.wait_for(

                asyncio.to_thread(
                    self.coletar_pjl
                ),

                timeout=TIMEOUT_PJL

            )

        except asyncio.TimeoutError:

            print(
                "[DEVICE] PJL excedeu o limite "
                f"de {TIMEOUT_PJL} segundos."
            )

        except Exception as erro:

            print(
                f"[DEVICE] Erro na coleta PJL: {erro}"
            )


        # ----------------------------------------------------
        # SEGUNDO: SNMP
        #
        # O resultado PJL já está armazenado.
        # ----------------------------------------------------

        try:

            await self.coletar_snmp()

        except Exception as erro:

            print(
                f"[DEVICE] Erro na coleta SNMP: {erro}"
            )


        return self.to_dict()


    # ========================================================
    # ESTADO
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
    # TOTAL SUPPLIES
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
                self.identificacao.copy(),

            "conectividade":
                self.conectividade.copy(),

            "supplies":
                list(
                    self.supplies
                ),

            "estado":
                self.estado(),

            "total_supplies":
                self.total_supplies()

        }


# ============================================================
# COMPATIBILIDADE
# ============================================================

Device = PrinterDevice


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

    print(
        "=" * 68
    )

    print(
        "PRINTER ASSISTANT - TESTE DEVICE"
    )

    print(
        "=" * 68
    )

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
        "Coletando dados PJL + SNMP..."
    )

    print()

    await device.coletar()

    dados = device.to_dict()

    identificacao = (
        dados["identificacao"]
    )

    conectividade = (
        dados["conectividade"]
    )

    print()

    print("=" * 68)

    print(
        "RESULTADO"
    )

    print("=" * 68)

    print()

    print(
        "IP:",
        device.ip
    )

    print(
        "Fabricante:",
        identificacao["fabricante"]
    )

    print(
        "Modelo:",
        identificacao["modelo"]
    )

    print(
        "Família:",
        identificacao["familia"]
    )

    print(
        "Tipo:",
        identificacao["tipo"]
    )

    print(
        "Serial:",
        identificacao["serial"]
    )

    contador = identificacao[
        "contador"
    ]

    if contador is None:

        print(
            "Contador: desconhecido"
        )

    else:

        print(
            "Contador:",
            f"{contador:,}".replace(
                ",",
                "."
            )
        )

    print()

    print(
        "PJL:",
        "ATIVO"
        if conectividade["pjl"]
        else
        "INATIVO"
    )

    print(
        "SNMP:",
        "ATIVO"
        if conectividade["snmp"]
        else
        "INATIVO"
    )

    print(
        "Estado:",
        dados["estado"]
    )

    print(
        "Suprimentos:",
        len(
            dados["supplies"]
        )
    )

    print()

    print("=" * 68)

    print(
        "SUPRIMENTOS"
    )

    print("=" * 68)

    if not device.supplies:

        print()

        print(
            "Nenhum suprimento encontrado."
        )

    else:

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
                "    Índice:",
                supply.get(
                    "indice"
                )
            )

            print(
                "    Capacidade:",
                supply.get(
                    "capacidade"
                )
            )

            print(
                "    Restante:",
                supply.get(
                    "restante"
                )
            )

            print(
                "    Consumido:",
                supply.get(
                    "consumido"
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

    print("=" * 68)

    print(
        "TESTE CONCLUÍDO"
    )

    print("=" * 68)

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            teste()
        )

    except KeyboardInterrupt:

        print()

        print(
            "Programa encerrado pelo usuário."
        )