from core.registry import registry


def abrir():

    registry.carregar()

    while True:

        print()

        print("==============================")
        print("COMANDOS")
        print("==============================")

        print()

        for codigo in sorted(registry.comandos):

            comando = registry.comandos[codigo]

            print(
                f"{codigo} - {comando.INFO['nome']}"
            )

        print()

        print("0 - Voltar")

        print()

        op = input("> ")

        if op == "0":

            return

        try:

            op = int(op)

        except:

            continue

        if op not in registry.comandos:

            continue

        registry.comandos[op].executar()