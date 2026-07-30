from core.device import PrinterDevice
from tools.network import scan_rede

import asyncio


RAW_PORT = 9100


async def discover_printers():

    print()

    print("Descobrindo impressoras...")

    base = "192.168.14"

    ips = scan_rede(base)

    printers = []

    for ip in ips:

        device = PrinterDevice(ip)

        try:

            await asyncio.to_thread(
                device.coletar_pjl
            )

        except Exception:

            continue

        if device.modelo() != "Desconhecido":

            printers.append(device)

    return printers