from core.contexto import obter_contexto


def testar():

    contexto = obter_contexto()

    status = contexto.get(

        "usb_host",

        "Não testado"

    )

    return f"""

USB HOST

Status:

{status}

Procedimento

1 Inserir pendrive FAT32

2 Confirmar detecção

3 Confirmar leitura

"""