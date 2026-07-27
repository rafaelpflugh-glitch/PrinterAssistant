from pysnmp.hlapi.v3arch.asyncio import *

import asyncio


IP = "192.168.14.134"


OID_SUPRIMENTOS = "1.3.6.1.2.1.43.11.1.1"


async def snmp_walk(oid):

    dados = {}

    iterator = walk_cmd(
        SnmpEngine(),
        CommunityData("public", mpModel=1),
        await UdpTransportTarget.create((IP,161)),
        ContextData(),
        ObjectType(
            ObjectIdentity(oid)
        )
    )


    async for (
        errorIndication,
        errorStatus,
        errorIndex,
        varBinds

    ) in iterator:


        if errorIndication:
            print(errorIndication)
            break


        elif errorStatus:
            print(errorStatus.prettyPrint())
            break


        else:

            for name,value in varBinds:

                dados[str(name)] = str(value)


    return dados



async def main():


    print("="*50)
    print("LEXMARK SUPPLY FILTER")
    print("="*50)


    dados = await snmp_walk(
        OID_SUPRIMENTOS
    )


    for oid,valor in dados.items():

        if any(x in valor.lower() for x in [
            "toner",
            "imagem",
            "unid"
        ]):

            print()
            print(
                oid,
                "=",
                valor
            )


    print()
    print("Total:",len(dados))



asyncio.run(main())