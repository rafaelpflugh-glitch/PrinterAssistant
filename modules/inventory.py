from core.device import PrinterDevice


async def inventariar(device: PrinterDevice):

    print()

    print(f"Inventariando {device.ip}")

    await device.coletar_snmp()

    return device