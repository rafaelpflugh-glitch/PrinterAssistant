import asyncio
from typing import Any


# ============================================================
# PRINTER ASSISTANT - LEXMARK SNMP
# ============================================================
#
# Coletor SNMP específico para suprimentos Lexmark.
#
# Consulta somente:
#
#   Printer-MIB
#   prtMarkerSuppliesTable
#
# Dados:
#
#   - descrição
#   - capacidade
#   - nível/restante
#   - percentual
#   - consumo
#   - status
#
# Compatível com PySNMP 7.x.
#
# ============================================================


SNMP_PORT = 161

SUPPLIES_BASE = "1.3.6.1.2.1.43.11.1.1"

OID_DESCRIPTION = f"{SUPPLIES_BASE}.6"
OID_MAX_CAPACITY = f"{SUPPLIES_BASE}.8"
OID_LEVEL = f"{SUPPLIES_BASE}.9"


# ============================================================
# UTILITÁRIOS
# ============================================================

def normalizar_texto(valor: Any) -> str:

    if valor is None:
        return ""

    texto = str(valor).strip()

    if texto.startswith("b'") and texto.endswith("'"):
        texto = texto[2:-1]

    return texto


def inteiro(valor: Any):

    try:
        return int(str(valor).strip())

    except Exception:
        return None


def calcular_percentual(nivel, capacidade):

    if nivel is None:
        return None

    if capacidade is None:
        return None

    if capacidade <= 0:
        return None

    if nivel < 0:
        return None

    percentual = (
        nivel / capacidade
    ) * 100

    return round(
        max(
            0,
            min(
                100,
                percentual
            )
        ),
        1
    )


def determinar_status(percentual):

    if percentual is None:
        return "DESCONHECIDO"

    if percentual <= 10:
        return "CRITICO"

    if percentual <= 30:
        return "BAIXO"

    if percentual <= 60:
        return "ATENCAO"

    return "BOM"


# ============================================================
# CONSULTAR UMA LINHA DA TABELA
# ============================================================

async def consultar_linha(
    snmp,
    auth,
    transport,
    context,
    indice
):
    """
    Consulta diretamente as três colunas necessárias
    para um determinado índice da Printer-MIB.

    Não faz WALK geral.
    """

    from pysnmp.hlapi.v3arch.asyncio import (
        ObjectType,
        ObjectIdentity,
        get_cmd,
    )

    objetos = [

        ObjectType(
            ObjectIdentity(
                f"{OID_DESCRIPTION}.{indice}"
            )
        ),

        ObjectType(
            ObjectIdentity(
                f"{OID_MAX_CAPACITY}.{indice}"
            )
        ),

        ObjectType(
            ObjectIdentity(
                f"{OID_LEVEL}.{indice}"
            )
        )

    ]

    (
        error_indication,
        error_status,
        error_index,
        var_binds
    ) = await get_cmd(

        snmp,
        auth,
        transport,
        context,
        *objetos

    )

    if error_indication:
        return None

    if error_status:
        return None

    if not var_binds:
        return None

    valores = []

    for oid, valor in var_binds:

        texto_oid = str(oid)
        texto_valor = str(valor).lower()

        if (
            "no such instance" in texto_valor
            or "no such object" in texto_valor
        ):
            return None

        valores.append(valor)

    if len(valores) != 3:
        return None

    descricao = normalizar_texto(
        valores[0]
    )

    capacidade = inteiro(
        valores[1]
    )

    nivel = inteiro(
        valores[2]
    )

    if (
        not descricao
        and capacidade is None
        and nivel is None
    ):
        return None

    percentual = calcular_percentual(
        nivel,
        capacidade
    )

    restante = None
    consumido = None

    if nivel is not None and nivel >= 0:

        restante = nivel

    if (
        capacidade is not None
        and nivel is not None
        and capacidade >= 0
        and nivel >= 0
    ):

        consumido = max(
            0,
            capacidade - nivel
        )

    return {

        "indice": str(indice),

        "nome": (
            descricao
            or f"Suprimento {indice}"
        ),

        "capacidade": capacidade,

        "restante": restante,

        "consumido": consumido,

        "nivel": percentual,

        "status": determinar_status(
            percentual
        )

    }


# ============================================================
# COLETOR PRINCIPAL
# ============================================================

async def coletar_supplies(
    ip,
    community="public",
    timeout=2,
    retries=0
):
    """
    Coleta suprimentos da impressora.

    Estratégia:

        1. Conecta via SNMP.
        2. Consulta índices 1..16.
        3. Para cada índice consulta somente:
           - description
           - max capacity
           - level
        4. Ignora entradas inexistentes.
        5. Retorna somente suprimentos válidos.

    Não faz SNMP WALK geral.
    """

    try:

        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine,
            UdpTransportTarget,
            CommunityData,
            ContextData,
        )

    except ImportError as erro:

        raise RuntimeError(
            "Falha ao importar PySNMP 7.x. "
            "Verifique o ambiente virtual."
        ) from erro

    engine = SnmpEngine()

    try:

        transport = await UdpTransportTarget.create(

            (
                ip,
                SNMP_PORT
            ),

            timeout=timeout,

            retries=retries

        )

        auth = CommunityData(
            community,
            mpModel=1
        )

        context = ContextData()

        # ----------------------------------------------------
        # A MX611 normalmente possui poucas entradas.
        #
        # Não fazemos WALK.
        #
        # Consultamos somente uma faixa pequena de índices.
        # ----------------------------------------------------

        indices = range(
            1,
            17
        )

        tarefas = [

            consultar_linha(

                engine,

                auth,

                transport,

                context,

                indice

            )

            for indice in indices

        ]

        resultados = await asyncio.gather(
            *tarefas,
            return_exceptions=True
        )

        supplies = []

        for resultado in resultados:

            if isinstance(
                resultado,
                Exception
            ):
                continue

            if resultado is None:
                continue

            supplies.append(
                resultado
            )

        supplies.sort(

            key=lambda item: (

                int(
                    item["indice"]
                )

                if str(
                    item["indice"]
                ).isdigit()

                else 999999

            )

        )

        return supplies

    finally:

        try:

            engine.close_dispatcher()

        except Exception:

            pass


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    async def teste():

        print(
            "=" * 68
        )

        print(
            "PRINTER ASSISTANT - TESTE SNMP LEXMARK"
        )

        print(
            "=" * 68
        )

        print()

        ip = input(
            "IP da impressora: "
        ).strip()

        print()

        print(
            "SNMP: consultando somente tabela de suprimentos..."
        )

        print()

        try:

            supplies = await coletar_supplies(
                ip
            )

        except Exception as erro:

            print()

            print(
                "ERRO SNMP:"
            )

            print(
                erro
            )

            return

        print()

        print(
            "=" * 68
        )

        print(
            "SUPRIMENTOS ENCONTRADOS"
        )

        print(
            "=" * 68
        )

        if not supplies:

            print()

            print(
                "Nenhum suprimento retornado pelo SNMP."
            )

            print()

            return

        for numero, item in enumerate(
            supplies,
            start=1
        ):

            print()

            print(
                f"[{numero}] {item['nome']}"
            )

            print(
                "    Índice:",
                item["indice"]
            )

            print(
                "    Capacidade:",
                item["capacidade"]
            )

            print(
                "    Restante:",
                item["restante"]
            )

            print(
                "    Consumido:",
                item["consumido"]
            )

            print(
                "    Nível:",
                item["nivel"],
                "%"
            )

            print(
                "    Status:",
                item["status"]
            )

        print()

        print(
            "=" * 68
        )

        print(
            "TESTE CONCLUÍDO"
        )

        print(
            "=" * 68
        )


    asyncio.run(
        teste()
    )