from pysnmp.hlapi.v3arch.asyncio import *
import asyncio


# ===============================
# CONFIGURAÇÃO
# ===============================

IP = "192.168.14.134"

COMMUNITY = "public"

BASE = "1.3.6.1.2.1.43.11.1.1"



# ===============================
# CORREÇÃO DE TEXTO LEXMARK
# ===============================

def corrigir_texto(texto):

    if texto is None:
        return "Desconhecido"


    # tenta corrigir mojibake comum de SNMP Lexmark

    substituicoes = {

        "‡Æ": "ÇÃ",
        "‡": "Ç",
        "Æ": "Ã",
        "": "Ç",
        "": "È",
        "": "É",
        "": "Ê",
        "": "Ë",
        "": "Ì",
        "": "Í",
        "": "Î",
        "": "Ï",
        "": "Ð",
        "": "Ñ",
        "": "Ò",
        "": "Ó",
        "": "Ô",
        "": "Õ",
        "": "Ö",
        "": "×",
        "": "Ø",
        "": "Ù",
        "": "Ú",
        "": "Û",
        "": "Ü",
        "": "Ý",

    }


    for errado,certo in substituicoes.items():

        texto = texto.replace(
            errado,
            certo
        )


    return texto



# ===============================
# SNMP WALK
# ===============================

async def snmp_walk():

    dados = {}


    iterator = walk_cmd(

        SnmpEngine(),

        CommunityData(
            COMMUNITY,
            mpModel=1
        ),

        await UdpTransportTarget.create(
            (IP,161)
        ),

        ContextData(),

        ObjectType(
            ObjectIdentity(BASE)
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
                "ERRO:",
                errorIndication
            )

            break



        if errorStatus:

            print(
                "ERRO SNMP:",
                errorStatus.prettyPrint()
            )

            break



        for oid,value in varBinds:

            dados[str(oid)] = str(value)



    return dados




# ===============================
# PARSER
# ===============================

def parse_supplies(dados):

    supplies = {}


    for oid,value in dados.items():


        if not oid.startswith(BASE):

            continue



        partes = oid.split(".")



        try:

            atributo = partes[-3]

            indice = partes[-1]


        except:

            continue



        if indice not in supplies:

            supplies[indice] = {}



        supplies[indice][atributo] = value



    return supplies




# ===============================
# MOSTRAR SUPPLIES
# ===============================

def mostrar_supplies(supplies):


    print("="*50)
    print("LEXMARK SUPPLY STATUS")
    print("="*50)



    for idx,item in supplies.items():


        nome = corrigir_texto(
            item.get(
                "6"
            )
        )


        capacidade = item.get(
            "8"
        )


        restante = item.get(
            "9"
        )



        print()

        print(
            nome.upper()
        )

        print(
            "-"*30
        )



        try:


            capacidade = int(
                capacidade
            )


            restante = int(
                restante
            )



            usado = capacidade - restante



            nivel = (
                restante /
                capacidade
            ) * 100



            print(
                f"Capacidade : {capacidade:,} páginas"
            )


            print(
                f"Restante   : {restante:,} páginas"
            )


            print(
                f"Uso        : {usado:,} páginas"
            )


            print(
                f"Nível      : {nivel:.1f}%"
            )



        except:


            print(
                "Sem dados de capacidade"
            )



    print()




# ===============================
# MAIN
# ===============================

async def main():


    dados = await snmp_walk()



    print()

    print(
        "Objetos SNMP encontrados:",
        len(dados)
    )



    supplies = parse_supplies(
        dados
    )



    mostrar_supplies(
        supplies
    )




# ===============================
# START
# ===============================

asyncio.run(main())