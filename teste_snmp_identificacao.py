import asyncio
from pysnmp.hlapi.v3arch.asyncio import *


IP = "192.168.14.134"


oids = {

    "Descricao": "1.3.6.1.2.1.1.1.0",

    "OID Sistema": "1.3.6.1.2.1.1.2.0",

    "Hostname": "1.3.6.1.2.1.1.5.0",

    "Modelo 1": "1.3.6.1.2.1.43.15.1.1.4.1.1",

    "Modelo 2": "1.3.6.1.2.1.43.15.1.1.4.1.2",

    "Modelo 3": "1.3.6.1.2.1.43.15.1.1.4.1.3",

}


async def snmp_get(oid):

    iterator = get_cmd(
        SnmpEngine(),
        CommunityData("public"),
        await UdpTransportTarget.create((IP,161)),
        ContextData(),
        ObjectType(
            ObjectIdentity(oid)
        )
    )


    errorIndication, errorStatus, errorIndex, varBinds = await iterator


    if errorIndication:
        return f"ERRO: {errorIndication}"


    elif errorStatus:
        return f"ERRO: {errorStatus}"


    else:

        for name, val in varBinds:
            return str(val)



async def main():

    print("="*40)
    print("IDENTIFICAÇÃO DA IMPRESSORA")
    print("="*40)


    for nome, oid in oids.items():

        valor = await snmp_get(oid)

        print(f"\n{nome}")
        print("OID:", oid)
        print("Valor:", valor)



asyncio.run(main())