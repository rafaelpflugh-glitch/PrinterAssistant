from tools.network import scan_rede
from core.device import PrinterDevice

import asyncio


RAW_PORT = 9100


async def descobrir(base):

    ips = scan_rede(base)

    encontrados = []

    for ip in ips:

        device = PrinterDevice(ip)

        await asyncio.to_thread(device.coletar_pjl)

        if device.identificacao["modelo"] != "Desconhecido":

            encontrados.append(device)

    return encontrados