import asyncio
import json

from core.snmp import SNMPPrinter


async def main():
    ip = "192.168.14.134"

    printer = SNMPPrinter(ip)

    await printer.coletar()

    print("=" * 80)
    print("RAW SUPPLIES")
    print("=" * 80)

    print(
        json.dumps(
            printer.raw_supplies,
            indent=2,
            ensure_ascii=False
        )
    )

    print()
    print("=" * 80)
    print("RAW IDENTIFICADORES")
    print("=" * 80)

    print(
        json.dumps(
            printer.raw_identificadores,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
