import asyncio

from core.device import PrinterDevice



TIMEOUT_SNMP = 45



# ============================================================
# INVENTÁRIO SNMP
# ============================================================

async def inventariar(device: PrinterDevice):


    print()

    print(
        f"[INVENTORY] Atualizando SNMP {device.ip}"
    )


    try:


        await asyncio.wait_for(

            device.coletar_snmp(),

            timeout=TIMEOUT_SNMP

        )


        if device.total_supplies():

            print(

                f"[INVENTORY] "
                f"{device.total_supplies()} suprimentos encontrados."

            )


        else:

            print(

                "[INVENTORY] "
                "SNMP respondeu sem suprimentos."

            )


    except asyncio.TimeoutError:


        print(

            f"[INVENTORY] Timeout SNMP {device.ip}"

        )


    except Exception as erro:


        print(

            f"[INVENTORY] Erro SNMP {device.ip}: {erro}"

        )


    return device




# ============================================================
# LISTA DE EQUIPAMENTOS
# ============================================================

async def inventariar_lista(dispositivos):


    tarefas = []


    for device in dispositivos:


        tarefas.append(

            inventariar(
                device
            )

        )


    await asyncio.gather(
        *tarefas
    )


    return dispositivos