import asyncio

from pysnmp.hlapi.v3arch.asyncio import *


IP = "192.168.14.134"


async def walk(oid):

    print("\nWALK:", oid)
    print("="*60)

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

        elif errorStatus:
            print(errorStatus)
            break

        else:

            for name,val in varBinds:
                print(
                    name,
                    "=",
                    val
                )


asyncio.run(
    walk(
        "1.3.6.1.2.1.43"
    )
)	