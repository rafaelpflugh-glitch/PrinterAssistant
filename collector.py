import asyncio
import json
import sys
from datetime import datetime

from pysnmp.hlapi.v3arch.asyncio import *

from core.pjl import coletar_identificacao



# ==================================================
# CONFIGURAÇÃO
# ==================================================

COMMUNITY = "public"

SNMP_BASE = "1.3.6.1.2.1.43.11.1.1"




# ==================================================
# LIMPEZA DE TEXTO
# ==================================================

def limpar_texto(texto):

    if not texto:
        return texto


    codigos = [

        "cp858",
        "cp850",
        "latin1",
        "utf-8"

    ]


    for codigo in codigos:

        try:

            return texto.encode(
                "latin1"
            ).decode(
                codigo
            )

        except:

            continue


    return texto




def normalizar_supply(nome):


    mapa = {

        "Kit manutenÆo":
        "Kit manutenção",

        "Kit manuten‡Æo":
        "Kit manutenção",

        "Unid. imagem":
        "Unidade de imagem",

        "Toner preto":
        "Toner preto"

    }


    return mapa.get(
        nome,
        nome
    )




# ==================================================
# SNMP WALK
# ==================================================

async def snmp_walk(ip):

    dados = {}


    iterator = walk_cmd(

        SnmpEngine(),

        CommunityData(

            COMMUNITY,

            mpModel=1

        ),


        await UdpTransportTarget.create(

            (ip,161),

            timeout=3,

            retries=1

        ),


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
                "Aviso SNMP:",
                errorIndication
            )

            break



        if errorStatus:

            break



        for oid,value in varBinds:

            dados[str(oid)] = str(value)



    return dados




# ==================================================
# PARSER SUPPLIES
# ==================================================

def parse_supplies(dados):


    tabela = {}



    for oid,value in dados.items():


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



        tabela[indice][atributo] = value




    resultado = []



    for item in tabela.values():


        nome = item.get("6")

        capacidade = item.get("8")

        restante = item.get("9")



        if not nome:

            continue



        nome = limpar_texto(nome)

        nome = normalizar_supply(nome)



        try:

            capacidade = int(capacidade)

            restante = int(restante)


        except:

            continue



        if capacidade <= 0:

            continue



        consumido = capacidade - restante


        nivel = round(

            (restante / capacidade)*100,

            1

        )


        if nivel >= 70:

            status="BOM"

        elif nivel >=40:

            status="ATENCAO"

        else:

            status="BAIXO"



        resultado.append({

            "nome":nome,

            "capacidade":capacidade,

            "restante":restante,

            "consumido":consumido,

            "nivel":nivel,

            "status":status

        })


    return resultado




# ==================================================
# MAIN
# ==================================================

async def main():


    if len(sys.argv) < 2:

        print()

        print(
            "Uso:"
        )

        print(
            "python collector.py IP_DA_IMPRESSORA"
        )

        print()

        return



    ip = sys.argv[1]



    print("="*60)

    print(
        "PRINTER ASSISTANT - COLETOR"
    )

    print("="*60)



    print()

    print(
        "Impressora:",
        ip
    )



    print()

    print(
        "Coletando SNMP..."
    )



    bruto = await snmp_walk(ip)



    supplies = parse_supplies(

        bruto

    )



    print(

        "Suprimentos encontrados:",

        len(supplies)

    )



    print()

    print(
        "Coletando PJL..."
    )



    identificacao = coletar_identificacao(

        ip

    )




    dados_final={


        "data":

        datetime.now().strftime(

            "%d/%m/%Y %H:%M:%S"

        ),


        "ip":

        ip,


        "identificacao":

        identificacao,


        "supplies":

        supplies


    }




    with open(

        "printer_data.json",

        "w",

        encoding="utf-8"

    ) as arquivo:


        json.dump(

            dados_final,

            arquivo,

            indent=4,

            ensure_ascii=False

        )




    print()

    print(
        "OK!"
    )

    print(
        "printer_data.json criado"
    )



asyncio.run(main())