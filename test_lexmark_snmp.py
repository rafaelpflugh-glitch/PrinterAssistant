import asyncio

from tools.lexmark_snmp import coletar_supplies


IP = "192.168.14.134"


async def main():

    print("=" * 68)
    print("PRINTER ASSISTANT - TESTE SNMP LEXMARK")
    print("=" * 68)

    print()

    print("Impressora:", IP)
    print("SNMP: consultando somente tabela de suprimentos...")
    print()

    try:

        supplies = await coletar_supplies(
            IP,
            community="public",
            timeout=2,
            retries=0
        )

    except Exception as erro:

        print()
        print("ERRO SNMP:")
        print(erro)

        return


    print()
    print("=" * 68)
    print("SUPRIMENTOS ENCONTRADOS")
    print("=" * 68)


    if not supplies:

        print()
        print("Nenhum suprimento retornado pelo SNMP.")
        print()

        return


    for numero, item in enumerate(
        supplies,
        start=1
    ):

        print()

        print(
            f"[{numero}] {item['nome']}"
        )

        print(
            "    Índice:",
            item["indice"]
        )

        print(
            "    Capacidade:",
            item["capacidade"]
        )

        print(
            "    Restante:",
            item["restante"]
        )

        print(
            "    Consumido:",
            item["consumido"]
        )

        print(
            "    Nível:",
            item["nivel"],
            "%"
        )

        print(
            "    Status:",
            item["status"]
        )


    print()
    print("=" * 68)
    print("TESTE CONCLUÍDO")
    print("=" * 68)


if __name__ == "__main__":

    asyncio.run(
        main()
    )