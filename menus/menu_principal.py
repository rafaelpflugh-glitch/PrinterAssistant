from core.state import state


def cabecalho():

    print()
    print("==========================================")
    print("        HERMES ASSISTENTE DE BANCADA")
    print("==========================================")
    print()

    if state.printer:

        print("Impressora atual")
        print("----------------")

        print("IP........:", state.printer.ip)
        print("Modelo....:", state.printer.modelo)
        print("Serial....:", state.printer.serial)
        print("Firmware..:", state.printer.firmware)

    else:

        print("Nenhuma impressora conectada.")

    print()


def menu():

    cabecalho()

    print("1 - Procurar impressoras")
    print("2 - Informações")
    print("3 - Comandos")
    print("4 - Rotinas")
    print("5 - Banco de dados")
    print("0 - Sair")
    print()

    return input("> ")