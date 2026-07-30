import asyncio
import json

from modules.discovery import descobrir, coletar_snmp


def menu(dispositivos):

    print()

    print("="*70)
    print("IMPRESSORAS ENCONTRADAS")
    print("="*70)


    for i,d in enumerate(dispositivos,1):

        print()

        print(
            f"[{i}] {d.modelo()} - {d.ip}"
        )


    print()

    escolha = input(
        "Escolha: "
    )


    try:

        return dispositivos[
            int(escolha)-1
        ]

    except:

        return None



async def main():

    print()

    print(
        "PRINTER ASSISTANT"
    )


    impressoras = await descobrir(
        "192.168.14"
    )


    if not impressoras:

        print(
            "Nenhuma encontrada."
        )

        return



    await coletar_snmp(
        impressoras
    )


    selecionada = menu(
        impressoras
    )


    if selecionada:

        dados = selecionada.to_dict()


        with open(
            "selected_printer.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                dados,
                f,
                indent=4,
                ensure_ascii=False
            )


        print()

        print(
            "Selecionada:"
        )

        print(
            json.dumps(
                dados,
                indent=4,
                ensure_ascii=False
            )
        )


        print()

        print(
            "Salvo selected_printer.json"
        )



if __name__ == "__main__":

    asyncio.run(main())