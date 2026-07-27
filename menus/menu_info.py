from core.state import state


def abrir():

    print()

    if state.printer is None:

        print("Nenhuma impressora selecionada.")
        input("\nENTER...")
        return


    p = state.printer

    print("==============================")
    print("INFORMAÇÕES")
    print("==============================")

    print("IP..........:", p.ip)
    print("Fabricante..:", p.fabricante)
    print("Modelo......:", p.modelo)
    print("Serial......:", p.serial)
    print("Firmware....:", p.firmware)

    input("\nENTER...")