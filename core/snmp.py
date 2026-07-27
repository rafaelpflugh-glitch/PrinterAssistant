import asyncio

from pysnmp.hlapi.v3arch.asyncio import *


# ============================================================
# PRINTER ASSISTANT - MÓDULO SNMP
# ============================================================
#
# Responsabilidade:
#
# - conectar via SNMP
# - coletar tabela de suprimentos
# - interpretar capacidade/restante
# - calcular consumo
# - calcular nível percentual
# - determinar status
#
# O IP NÃO é fixo.
# O IP é recebido pela função coletar_supplies().
# ============================================================


COMMUNITY = "public"

SNMP_PORTA = 161

TIMEOUT = 3

RETRIES = 1


# ============================================================
# OID BASE - PRINTER-MIB
# ============================================================

SNMP_BASE = "1.3.6.1.2.1.43.11.1.1"


# ============================================================
# LIMPEZA DE TEXTO
# ============================================================

def limpar_texto(texto):

    if not texto:
        return texto


    # Primeiro tentamos corrigir os casos conhecidos
    # de texto recebido como Latin-1 e interpretado
    # incorretamente.

    tentativas = [

        ("latin1", "utf-8"),

        ("cp850", "utf-8"),

        ("cp858", "utf-8"),

    ]


    for origem, destino in tentativas:

        try:

            corrigido = texto.encode(
                origem
            ).decode(
                destino
            )


            # Só aceitamos a conversão se ela
            # realmente produzir algo utilizável.

            if corrigido:

                return corrigido


        except:

            pass


    return texto


# ============================================================
# NORMALIZAÇÃO DOS NOMES
# ============================================================

def normalizar_supply(nome):

    if not nome:
        return nome


    nome = nome.strip()


    # Casos conhecidos da Lexmark
    mapa = {

        "Toner preto":
            "Toner preto",

        "Unid. imagem":
            "Unidade de imagem",

        "Unidade de imagem":
            "Unidade de imagem",

        "Kit manutenção":
            "Kit manutenção",

        "Kit manutenÆo":
            "Kit manutenção",

        "Kit manuten‡Æo":
            "Kit manutenção",

    }


    if nome in mapa:

        return mapa[nome]


    return nome


# ============================================================
# CLASSIFICAÇÃO DO STATUS
# ============================================================

def determinar_status(nivel):

    if nivel >= 70:

        return "BOM"


    elif nivel >= 40:

        return "ATENCAO"


    else:

        return "BAIXO"


# ============================================================
# WALK SNMP
# ============================================================

async def snmp_walk(ip):

    dados = {}


    try:

        transport = await UdpTransportTarget.create(

            (
                ip,
                SNMP_PORTA
            ),

            timeout=TIMEOUT,

            retries=RETRIES

        )


        iterator = walk_cmd(

            SnmpEngine(),

            CommunityData(

                COMMUNITY,

                mpModel=1

            ),

            transport,

            ContextData(),

            ObjectType(

                ObjectIdentity(

                    SNMP_BASE

                )

            )

        )


        async for (

            errorIndication,

            errorStatus,

            errorIndex,

            varBinds

        ) in iterator:


            if errorIndication:

                print(
                    f"[SNMP] Aviso em {ip}: "
                    f"{errorIndication}"
                )

                break


            if errorStatus:

                print(
                    f"[SNMP] Erro em {ip}: "
                    f"{errorStatus.prettyPrint()}"
                )

                break


            for oid, value in varBinds:

                dados[str(oid)] = str(value)


    except Exception as erro:

        print(
            f"[SNMP] Falha em {ip}: {erro}"
        )


    return dados


# ============================================================
# PARSER DA TABELA DE SUPRIMENTOS
# ============================================================

def parse_supplies(dados):

    tabela = {}


    for oid, value in dados.items():


        if not oid.startswith(
            SNMP_BASE
        ):

            continue


        partes = oid.split(".")


        try:

            # Estrutura do Printer-MIB:
            #
            # ...43.11.1.1.<atributo>.<indice>
            #
            # Atributos utilizados:
            #
            # 6 = descrição
            # 8 = capacidade
            # 9 = nível/restante

            atributo = partes[-2]

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


        tabela[indice][atributo] = value


    resultado = []


    for indice, item in tabela.items():


        nome = item.get("6")

        capacidade = item.get("8")

        restante = item.get("9")


        if not nome:

            continue


        nome = limpar_texto(
            nome
        )


        nome = normalizar_supply(
            nome
        )


        try:

            capacidade = int(
                capacidade
            )

            restante = int(
                restante
            )


        except:

            continue


        if capacidade <= 0:

            continue


        # Algumas impressoras podem retornar
        # valores negativos ou acima da capacidade.

        if restante < 0:

            restante = 0


        if restante > capacidade:

            restante = capacidade


        consumido = (
            capacidade - restante
        )


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


        status = determinar_status(
            nivel
        )


        resultado.append({

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
# COLETAR SUPRIMENTOS
# ============================================================

async def coletar_supplies(ip):

    print(
        f"[SNMP] Coletando suprimentos de {ip}..."
    )


    dados = await snmp_walk(
        ip
    )


    if not dados:

        return []


    supplies = parse_supplies(
        dados
    )


    return supplies


# ============================================================
# ALIAS EM PORTUGUÊS
# ============================================================
#
# Mantemos esse nome também para facilitar futuras
# integrações e deixar a API do módulo mais flexível.
# ============================================================

async def coletar_suprimentos(ip):

    return await coletar_supplies(
        ip
    )


# ============================================================
# TESTE DIRETO
# ============================================================

async def main():

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


    supplies = await coletar_supplies(
        ip
    )


    print()

    print("=" * 60)

    print(
        "RESULTADO"
    )

    print("=" * 60)


    if not supplies:

        print(
            "Nenhum suprimento encontrado."
        )

        return


    print(
        f"Suprimentos monitorados: "
        f"{len(supplies)}"
    )


    print()


    for numero, supply in enumerate(
        supplies,
        start=1
    ):


        print(
            f"[{numero}] "
            f"{supply['nome']}"
        )


        print(
            f"    Capacidade: "
            f"{supply['capacidade']}"
        )


        print(
            f"    Restante: "
            f"{supply['restante']}"
        )


        print(
            f"    Consumido: "
            f"{supply['consumido']}"
        )


        print(
            f"    Nível: "
            f"{supply['nivel']}%"
        )


        print(
            f"    Status: "
            f"{supply['status']}"
        )


        print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )