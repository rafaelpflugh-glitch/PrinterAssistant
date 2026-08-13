import asyncio

from core.snmp import SNMPPrinter


async def main():

    ip = "192.168.14.134"

    printer = SNMPPrinter(ip)

    print("=" * 60)
    print("SNMP WALK SUPPLIES")
    print("=" * 60)

    dados = await printer.walk(
        "1.3.6.1.2.1.43"
    )


    print()

    print(
        "TOTAL OIDS:",
        len(dados)
    )

    print()


    for oid, valor in dados.items():

        print(
            oid,
            "=",
            valor
        )


asyncio.run(main())