import asyncio

from core.snmp import SNMPPrinter


async def teste():

    p = SNMPPrinter(
        "192.168.14.134"
    )

    dados = await p.walk(
        "1.3.6.1.2.1.43"
    )

    for oid, valor in dados.items():

        print(
            oid,
            "=",
            valor
        )


asyncio.run(teste())