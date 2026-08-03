from workflow.routine import Routine


def criar_rotina():

    r = Routine("MX511 - Reset Completo")

    r.adicionar(
        "Reset contador Kit Manutenção ADF"
    )

    r.adicionar(
        "Reset contador Manutenção"
    )

    r.adicionar(
        "Reset Printer Settings"
    )

    r.adicionar(
        "Reset Network Settings"
    )

    r.adicionar(
        "Reset Apps"
    )

    r.adicionar(
        "Apagar memória"
    )

    r.adicionar(
        "Apagar Fora de Serviço"
    )

    r.adicionar(
        "Downgrade Firmware",
        "Selecionar firmware correto antes da instalação."
    )

    return r