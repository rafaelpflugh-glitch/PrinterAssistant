import asyncio
import json

from modules.discovery import descobrir
from modules.inventory import inventariar_lista



# ============================================================
# MOSTRAR EQUIPAMENTO
# ============================================================

def mostrar_equipamento(device):


    dados = device.to_dict()


    ident = dados["identificacao"]

    conexao = dados["conectividade"]

    supplies = dados["supplies"]



    print()

    print("=" * 70)
    print("EQUIPAMENTO SELECIONADO")
    print("=" * 70)


    print()

    print(
        f"Fabricante : {ident.get('fabricante')}"
    )

    print(
        f"Modelo     : {ident.get('modelo')}"
    )

    print(
        f"Família    : {ident.get('familia')}"
    )

    print(
        f"Tipo       : {ident.get('tipo')}"
    )

    print(
        f"Serial     : {ident.get('serial')}"
    )


    contador = ident.get(
        "contador"
    )


    if contador:

        contador = (
            f"{contador:,}"
            .replace(
                ",",
                "."
            )
        )


    else:

        contador = "Desconhecido"


    print(
        f"Contador   : {contador}"
    )


    print()

    print(
        "CONECTIVIDADE"
    )

    print("-"*70)


    for chave, valor in conexao.items():

        if isinstance(valor,bool):

            valor = (
                "ATIVO"
                if valor
                else
                "INATIVO"
            )


        print(
            f"{chave.upper():12}: {valor}"
        )



    print()

    print(
        "SUPRIMENTOS"
    )

    print("-"*70)



    if not supplies:


        print(
            "Nenhum suprimento."
        )


    for s in supplies:


        print()

        print(
            s["nome"]
        )


        print(
            "  Capacidade:",
            s["capacidade"]
        )

        print(
            "  Restante:",
            s["restante"]
        )

        print(
            "  Nível:",
            s["nivel"],
            "%"
        )


        print(
            "  Status:",
            s["status"]
        )



    print()

    print(
        "Estado:",
        dados["estado"]
    )


    print()

    print("="*70)




# ============================================================
# MENU
# ============================================================

def menu(lista):


    print()

    print("="*70)
    print("IMPRESSORAS ENCONTRADAS")
    print("="*70)



    for i,device in enumerate(lista,1):


        print(

            f"[{i}] "
            f"{device.modelo()} "
            f"- {device.ip}"

        )



    print()


    escolha=input(
        "Escolha: "
    )


    try:

        return lista[
            int(escolha)-1
        ]


    except:


        return None




# ============================================================
# MAIN
# ============================================================

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
            "Nenhuma impressora encontrada."
        )

        return



    await inventariar_lista(
    impressoras
)



    selecionada = menu(
        impressoras
    )



    if not selecionada:


        print(
            "Cancelado."
        )

        return



    mostrar_equipamento(
        selecionada
    )



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
        "Salvo selected_printer.json"
    )





if __name__=="__main__":


    asyncio.run(
        main()
    )