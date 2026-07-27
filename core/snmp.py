import asyncio

from pysnmp.hlapi.v3arch.asyncio import *


# ============================================================
# PRINTER ASSISTANT - MÓDULO SNMP
# ============================================================
#
# Responsabilidades:
#
# - comunicação SNMP
# - identificação básica
# - coleta de suprimentos
# - leitura de capacidade
# - leitura de restante
# - cálculo do nível
# - classificação do estado
#
# O IP é sempre recebido como argumento.
# Não existe impressora/IP fixo neste módulo.
# ============================================================


COMMUNITY_PADRAO = "public"

TIMEOUT_PADRAO = 2

RETRIES_PADRAO = 1


# ============================================================
# OIDs
# ============================================================

OID_SYS_DESCRICAO = (
    "1.3.6.1.2.1.1.1.0"
)


# Printer-MIB
OID_SUPPLIES_BASE = (
    "1.3.6.1.2.1.43.11.1.1"
)


# ============================================================
# CLASSE SNMP
# ============================================================

class SNMPPrinter:

    def __init__(
        self,
        ip,
        community=COMMUNITY_PADRAO,
        timeout=TIMEOUT_PADRAO,
        retries=RETRIES_PADRAO
    ):

        self.ip = ip

        self.community = community

        self.timeout = timeout

        self.retries = retries


    # ========================================================
    # GET
    # ========================================================

    async def get(self, oid):

        try:

            resultado = await get_cmd(

                SnmpEngine(),

                CommunityData(

                    self.community,

                    mpModel=1

                ),

                await UdpTransportTarget.create(

                    (
                        self.ip,
                        161
                    ),

                    timeout=self.timeout,

                    retries=self.retries

                ),

                ContextData(),

                ObjectType(

                    ObjectIdentity(
                        oid
                    )

                )

            )


            (
                error_indication,
                error_status,
                error_index,
                var_binds

            ) = resultado


            if error_indication:

                return None


            if error_status:

                return None


            for oid_resultado, valor in var_binds:

                return str(valor)


        except Exception:

            return None


        return None


    # ========================================================
    # WALK
    # ========================================================

    async def walk(self, oid_base):

        dados = {}


        try:

            iterator = walk_cmd(

                SnmpEngine(),

                CommunityData(

                    self.community,

                    mpModel=1

                ),

                await UdpTransportTarget.create(

                    (
                        self.ip,
                        161
                    ),

                    timeout=self.timeout,

                    retries=self.retries

                ),

                ContextData(),

                ObjectType(

                    ObjectIdentity(
                        oid_base
                    )

                )

            )


            async for (

                error_indication,

                error_status,
                error_index,
                var_binds

            ) in iterator:


                if error_indication:

                    break


                if error_status:

                    break


                for oid, valor in var_binds:

                    dados[
                        str(oid)
                    ] = str(valor)


        except Exception:

            pass


        return dados


    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    async def identificacao(self):

        descricao = await self.get(
            OID_SYS_DESCRICAO
        )


        return {

            "snmp": descricao is not None,

            "descricao": descricao

        }


    # ========================================================
    # SUPPLIES
    # ========================================================

    async def supplies(self):

        dados = await self.walk(
            OID_SUPPLIES_BASE
        )


        return parse_supplies(
            dados
        )


    # ========================================================
    # COLETA COMPLETA
    # ========================================================

    async def coletar(self):

        identificacao = await self.identificacao()

        supplies = await self.supplies()


        return {

            "ip": self.ip,

            "snmp": identificacao["snmp"],

            "descricao": identificacao["descricao"],

            "supplies": supplies

        }


# ============================================================
# LIMPEZA DE TEXTO
# ============================================================

def limpar_texto(texto):

    if not texto:

        return texto


    tentativas = [

        ("latin1", "utf-8"),

        ("cp850", "utf-8"),

        ("cp858", "utf-8")

    ]


    for origem, destino in tentativas:

        try:

            convertido = texto.encode(
                origem
            ).decode(
                destino
            )


            if convertido.count("�") == 0:

                return convertido


        except:

            pass


    return texto


# ============================================================
# NORMALIZAÇÃO DOS NOMES
# ============================================================

def normalizar_supply(nome):

    if not nome:

        return nome


    nome = limpar_texto(
        nome
    )


    mapa = {

        "Toner preto":
            "Toner preto",

        "Black Toner":
            "Toner preto",

        "Unid. imagem":
            "Unidade de imagem",

        "Unidade de imagem":
            "Unidade de imagem",

        "Imaging Unit":
            "Unidade de imagem",

        "Kit manutenção":
            "Kit manutenção",

        "Kit de manutenção":
            "Kit manutenção",

        "Maintenance Kit":
            "Kit manutenção",

        "Kit manutenÆo":
            "Kit manutenção",

        "Kit manuten‡Æo":
            "Kit manutenção"

    }


    return mapa.get(
        nome,
        nome
    )


# ============================================================
# STATUS DO SUPRIMENTO
# ============================================================

def calcular_status(nivel):

    if nivel >= 70:

        return "BOM"


    if nivel >= 40:

        return "ATENCAO"


    return "BAIXO"


# ============================================================
# PARSER DOS SUPRIMENTOS
# ============================================================

def parse_supplies(dados):

    tabela = {}


    # --------------------------------------------------------
    # IMPORTANTE
    #
    # Nesta impressora a estrutura retornada pelo walk é:
    #
    # 1.3.6.1.2.1.43.11.1.1.6.1
    #                              ↑
    #                            índice
    #
    # O atributo está três posições antes do final.
    #
    # 6 = descrição
    # 8 = capacidade máxima
    # 9 = quantidade restante
    #
    # NÃO alterar para partes[-2].
    # --------------------------------------------------------

    for oid, valor in dados.items():


        if not oid.startswith(
            OID_SUPPLIES_BASE
        ):

            continue


        partes = oid.split(".")


        try:

            atributo = partes[-3]

            indice = partes[-1]


        except:

            continue


        if atributo not in (

            "6",
            "8",
            "9"

        ):

            continue


        if indice not in tabela:

            tabela[indice] = {}


        tabela[indice][
            atributo
        ] = valor


    resultado = []


    # ========================================================
    # CONVERTE CADA SUPRIMENTO
    # ========================================================

    for indice, item in tabela.items():

        nome = item.get(
            "6"
        )


        capacidade = item.get(
            "8"
        )


        restante = item.get(
            "9"
        )


        if not nome:

            continue


        nome = normalizar_supply(
            nome
        )


        # ----------------------------------------------------
        # Conversão numérica
        # ----------------------------------------------------

        try:

            capacidade = int(
                capacidade
            )

            restante = int(
                restante
            )

        except:

            continue


        # ----------------------------------------------------
        # Dados inválidos
        # ----------------------------------------------------

        if capacidade <= 0:

            continue


        if restante < 0:

            restante = 0


        if restante > capacidade:

            restante = capacidade


        # ----------------------------------------------------
        # Consumo
        # ----------------------------------------------------

        consumido = (

            capacidade
            -
            restante

        )


        # ----------------------------------------------------
        # Percentual
        # ----------------------------------------------------

        nivel = round(

            (

                restante
                /
                capacidade

            )
            *
            100,

            1

        )


        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = calcular_status(
            nivel
        )


        resultado.append({

            "indice":
                indice,

            "nome":
                nome,

            "capacidade":
                capacidade,

            "restante":
                restante,

            "consumido":
                consumido,

            "nivel":
                nivel,

            "status":
                status

        })


    return resultado


# ============================================================
# FUNÇÃO DE CONVENIÊNCIA
# ============================================================

async def coletar_snmp(

    ip,

    community=COMMUNITY_PADRAO

):

    impressora = SNMPPrinter(

        ip=ip,

        community=community

    )


    return await impressora.coletar()


# ============================================================
# ALIAS PARA O COLLECTOR
# ============================================================
#
# O collector.py pode utilizar:
#
# from core.snmp import coletar_supplies
#
# Mantemos essa função explicitamente para evitar
# incompatibilidade entre os módulos.
# ============================================================

async def coletar_supplies(

    ip,

    community=COMMUNITY_PADRAO

):

    impressora = SNMPPrinter(

        ip=ip,

        community=community

    )


    return await impressora.supplies()


# ============================================================
# TESTE DIRETO
# ============================================================

async def teste():

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE SNMP"
    )

    print("=" * 60)


    ip = input(
        "\nDigite o IP da impressora: "
    ).strip()


    if not ip:

        print(
            "IP não informado."
        )

        return


    print()

    print(
        f"Testando SNMP em {ip}:161..."
    )


    impressora = SNMPPrinter(
        ip
    )


    dados = await impressora.coletar()


    print()

    print("=" * 60)

    print(
        "RESULTADO SNMP"
    )

    print("=" * 60)


    print()

    print(
        "IP:",
        dados["ip"]
    )


    print(
        "SNMP:",
        "ATIVO"
        if dados["snmp"]
        else "INATIVO"
    )


    print(
        "Descrição:",
        dados["descricao"]
    )


    print()

    print(
        "SUPRIMENTOS:"
    )


    if not dados["supplies"]:

        print(
            "Nenhum suprimento encontrado."
        )


    else:

        print(
            f"Total: "
            f"{len(dados['supplies'])}"
        )


        for numero, supply in enumerate(

            dados["supplies"],

            start=1

        ):

            print()

            print(
                f"[{numero}] "
                f"{supply['nome']}"
            )

            print(
                "    Capacidade:",
                supply["capacidade"]
            )

            print(
                "    Restante:",
                supply["restante"]
            )

            print(
                "    Consumido:",
                supply["consumido"]
            )

            print(
                "    Nível:",
                f'{supply["nivel"]}%'
            )

            print(
                "    Status:",
                supply["status"]
            )


    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        teste()
    )