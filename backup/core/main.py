import asyncio
import json

from scanner import procurar


# ==================================================
# MENU PRINCIPAL
# ==================================================

def mostrar_menu(impressoras):

    print()

    print("="*60)
    print("PRINTER ASSISTANT - SELEÇÃO DE EQUIPAMENTO")
    print("="*60)

    for i, printer in enumerate(impressoras):

        print()

        print(
            f"{i+1} - "
            f"{printer['fabricante']} "
            f"- {printer['ip']}"
        )


    print()

    escolha = input(
        "Escolha a impressora: "
    )


    try:

        indice = int(escolha)-1

        return impressoras[indice]


    except:

        return None



# ==================================================
# EXECUÇÃO
# ==================================================

async def main():


    impressoras = await procurar()


    if not impressoras:

        print(
            "Nenhuma impressora encontrada"
        )

        return



    selecionada = mostrar_menu(
        impressoras
    )



    if selecionada:


        print()

        print("="*60)

        print("EQUIPAMENTO SELECIONADO")

        print("="*60)


        print(
            json.dumps(
                selecionada,
                indent=4,
                ensure_ascii=False
            )
        )


        with open(
            "selected_printer.json",
            "w",
            encoding="utf-8"
        ) as f:


            json.dump(
                selecionada,
                f,
                indent=4,
                ensure_ascii=False
            )


        print()

        print(
            "Salvo em selected_printer.json"
        )



if __name__ == "__main__":

    asyncio.run(main())