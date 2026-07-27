import asyncio
from pysnmp.hlapi.v3arch.asyncio import *

IP = "192.168.14.134"


async def main():

    iterator = get_cmd(
        SnmpEngine(),
        CommunityData("public"),
        await UdpTransportTarget.create((IP, 161)),
        ContextData(),
        ObjectType(
            ObjectIdentity(
                "1.3.6.1.2.1.1.5.0"
            )
        )
    )

    errorIndication, errorStatus, errorIndex, varBinds = await iterator

    if errorIndication:
        print(errorIndication)

    elif errorStatus:
        print(errorStatus)

    else:
        for name, val in varBinds:
            print(name, "=", val)


asyncio.run(main())