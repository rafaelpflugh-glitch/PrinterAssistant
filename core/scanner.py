import socket
import asyncio
import json
import ipaddress

from pysnmp.hlapi.v3arch.asyncio import *

COMMUNITY = "public"

TIMEOUT = 0.5


# ==========================================================
# DESCOBRIR REDE
# ==========================================================

def descobrir_rede():

    host = socket.gethostbyname(socket.gethostname())

    rede = ".".join(host.split(".")[:3])

    return rede + ".0/24"


# ==========================================================
# TESTE PORTA
# ==========================================================

async def testar_porta(ip, porta):

    try:

        reader, writer = await asyncio.wait_for(

            asyncio.open_connection(ip, porta),

            timeout=TIMEOUT

        )

        writer.close()

        await writer.wait_closed()

        return True

    except:

        return False


# ==========================================================
# SNMP
# ==========================================================

async def testar_snmp(ip):

    try:

        resposta = await get_cmd(

            SnmpEngine(),

            CommunityData(COMMUNITY, mpModel=1),

            await UdpTransportTarget.create(

                (ip, 161),

                timeout=1,

                retries=0

            ),

            ContextData(),

            ObjectType(

                ObjectIdentity(

                    "1.3.6.1.2.1.1.1.0"

                )

            )

        )

        erro, status, indice, binds = resposta

        if erro:

            return None

        if status:

            return None

        for oid, valor in binds:

            return str(valor)

    except:

        return None

    return None


# ==========================================================
# ANALISAR UM IP
# ==========================================================

async def analisar_ip(ip):

    web, raw, ipp = await asyncio.gather(

        testar_porta(ip, 80),

        testar_porta(ip, 9100),

        testar_porta(ip, 631)

    )

    if not (web or raw or ipp):

        return None

    snmp = await testar_snmp(ip)

    return {

        "ip": ip,

        "web": web,

        "raw": raw,

        "ipp": ipp,

        "snmp": snmp

    }


# ==========================================================
# SCAN
# ==========================================================

async def procurar():

    rede = descobrir_rede()

    print("=" * 60)

    print("PRINTER ASSISTANT - SCANNER")

    print("=" * 60)

    print()

    print("Rede:", rede)

    print()

    print("Escaneando...")

    tarefas = []

    for ip in ipaddress.ip_network(rede).hosts():

        tarefas.append(

            analisar_ip(str(ip))

        )

    resultados = await asyncio.gather(*tarefas)

    encontrados = []

    for r in resultados:

        if r:

            encontrados.append(r)

    with open(

        "printers_found.json",

        "w",

        encoding="utf-8"

    ) as arq:

        json.dump(

            encontrados,

            arq,

            indent=4,

            ensure_ascii=False

        )

    print()

    print("=" * 60)

    print("DISPOSITIVOS")

    print("=" * 60)

    print()

    for d in encontrados:

        print(d["ip"])

    print()

    print(len(encontrados), "dispositivos encontrados")

    print()

    print("Arquivo salvo:")

    print("printers_found.json")


asyncio.run(procurar())