import asyncio

from core.snmp import SNMPPrinter


IP = "192.168.14.134"


async def main():

    printer = SNMPPrinter(IP)

    print("=" * 80)
    print("DUMP COMPLETO PRINTER-MIB")
    print("=" * 80)
    print()

    dados = await printer.walk(
        "1.3.6.1.2.1.43.11.1.1"
    )

    for oid, valor in dados.items():

        print(
            f"{oid} = {valor}"
        )


if __name__ == "__main__":

    asyncio.run(main())