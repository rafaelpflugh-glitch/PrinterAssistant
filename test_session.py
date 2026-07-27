import asyncio

from core.device import PrinterDevice
from core.session import PrinterSession


# ============================================================
# TESTE SESSION
# ============================================================

IP = "192.168.14.134"


async def main():

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE DE SESSÃO"
    )

    print("=" * 60)


    print()

    print(
        "Criando dispositivo..."
    )


    device = PrinterDevice(
        ip=IP
    )


    print(
        "Coletando dados..."
    )


    await device.coletar()


    print()

    print(
        "Criando sessão..."
    )


    sessao = PrinterSession()


    sessao.ativar(
        device
    )


    print()

    print("=" * 60)

    print(
        "IMPRESSORA ATIVA"
    )

    print("=" * 60)


    print()

    resumo = sessao.resumo()


    print(
        "Fabricante:",
        resumo["fabricante"]
    )


    print(
        "Modelo:",
        resumo["modelo"]
    )


    print(
        "Serial:",
        resumo["serial"]
    )


    contador = resumo["contador"]


    if contador is None:

        print(
            "Contador: desconhecido"
        )

    else:

        print(

            "Contador:",

            f"{contador:,}".replace(
                ",",
                "."
            )

        )


    print()

    print(
        "Estado:",
        resumo["estado"]
    )


    print(
        "Suprimentos:",
        resumo["supplies"]
    )


    print()

    print(
        "Sessão salva em:"
    )


    print(
        sessao.SESSION_FILE
        if hasattr(
            sessao,
            "SESSION_FILE"
        )
        else "C:\\PrinterAssistant\\session.json"
    )


    print()


if __name__ == "__main__":

    asyncio.run(
        main()
    )