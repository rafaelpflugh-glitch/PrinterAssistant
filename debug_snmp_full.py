import asyncio

from core.snmp import SNMPPrinter


IP = "192.168.14.134"


async def main():

    printer = SNMPPrinter(IP)


    print("=" * 80)
    print("DUMP SNMP COMPLETO")
    print("=" * 80)


    dados = await printer.walk(
        "1.3.6.1.2.1.43"
    )


    for oid, valor in dados.items():

        print(
            oid,
            "=",
            valor
        )


if __name__ == "__main__":

    asyncio.run(main())