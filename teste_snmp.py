from pysnmp.hlapi.v3arch.asyncio import *

import asyncio


ip = "192.168.14.134"

community = "public"

arquivo = "snmp_lexmark_walk.txt"


async def walk(oid):

    print("=" * 50)
    print(" SNMP LEXMARK WALK ")
    print("=" * 50)

    print("IP:", ip)
    print("OID:", oid)


    f = open(
        arquivo,
        "w",
        encoding="utf-8"
    )


    contador = 0


    async for (
        errorIndication,
        errorStatus,
        errorIndex,
        varBinds
    ) in walk_cmd(

        SnmpEngine(),

        CommunityData(
            community
        ),

        await UdpTransportTarget.create(
            (ip,161)
        ),

        ContextData(),

        ObjectType(
            ObjectIdentity(oid)
        ),

        lexicographicMode=False
    ):


        if errorIndication:

            print(
                "ERRO:",
                errorIndication
            )

            break


        elif errorStatus:

            print(
                errorStatus.prettyPrint()
            )

            break


        else:

            for name,value in varBinds:

                linha = (
                    name.prettyPrint()
                    +
                    " = "
                    +
                    value.prettyPrint()
                )

                print(linha)

                f.write(
                    linha
                    +
                    "\n"
                )

                contador += 1


    f.close()


    print()
    print("Finalizado")
    print(
        "Registros:",
        contador
    )


asyncio.run(
    walk(
        "1.3.6.1.2.1.43"
    )
)