import asyncio

from pysnmp.hlapi.v3arch.asyncio import *


IP = "192.168.14.134"


async def walk_suprimentos():

    oid = "1.3.6.1.2.1.43.11"

    print("=== SUPRIMENTOS LEXMARK ===")
    print("="*70)


    iterator = walk_cmd(
        SnmpEngine(),
        CommunityData("public"),
        await UdpTransportTarget.create((IP,161)),
        ContextData(),
        ObjectType(
            ObjectIdentity(oid)
        ),
        lexicographicMode=False
    )


    async for errorIndication, errorStatus, errorIndex, varBinds in iterator:

        if errorIndication:
            print(errorIndication)
            break

        if errorStatus:
            print(errorStatus)
            break


        for name, value in varBinds:

            print(
                f"{name} = {value}"
            )


asyncio.run(walk_suprimentos())