import asyncio

from tools.network import scan_rede
from core.device import PrinterDevice


async def descobrir(base):

    print()
    print("="*70)
    print("DISCOVERY - PRINTER ASSISTANT")
    print("="*70)

    print()
    print("Escaneando rede...")

    ips = scan_rede(base)

    print()
    print(f"{len(ips)} hosts ativos encontrados.")

    candidatos = []

    print()
    print("Testando PJL...")

    for ip in ips:

        device = PrinterDevice(ip)

        try:

            await asyncio.to_thread(
                device.coletar_pjl
            )

        except Exception:

            continue


        modelo = device.identificacao.get(
            "modelo",
            "Desconhecido"
        )


        serial = device.identificacao.get(
            "serial",
            "Desconhecido"
        )


        if (
            modelo != "Desconhecido"
            or
            serial != "Desconhecido"
        ):

            candidatos.append(device)


    print()

    print(
        f"{len(candidatos)} impressora(s) encontrada(s)."
    )


    return candidatos



async def coletar_snmp(dispositivos):

    print()
    print("Consultando SNMP...")


    for device in dispositivos:

        try:

            await asyncio.to_thread(
                device.coletar_snmp
            )

        except Exception as erro:

            print(
                f"SNMP falhou {device.ip}: {erro}"
            )


    return dispositivos