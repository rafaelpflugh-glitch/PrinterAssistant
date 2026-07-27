def mostrar_supplies(supplies):

    print("="*50)
    print("LEXMARK SUPPLY STATUS")
    print("="*50)


    for idx, item in supplies.items():

        nome = item.get("6", "Desconhecido")

        capacidade = item.get("8")
        restante = item.get("9")


        print()
        print(nome.upper())
        print("-"*30)


        if capacidade and restante:

            capacidade = int(capacidade)
            restante = int(restante)


            usado = capacidade - restante

            percentual = (
                restante / capacidade
            ) * 100


            print(
                f"Capacidade : {capacidade:,} páginas"
            )

            print(
                f"Restante   : {restante:,} páginas"
            )

            print(
                f"Uso        : {usado:,} páginas"
            )

            print(
                f"Nível      : {percentual:.1f}%"
            )

        else:

            print(
                "Sem dados de capacidade"
            )