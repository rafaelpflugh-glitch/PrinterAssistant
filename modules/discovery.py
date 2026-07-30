import asyncio

from tools.network import scan_rede
from core.device import PrinterDevice


TIMEOUT_PJL = 15


# ============================================================
# DISCOVERY
# ============================================================

async def descobrir(base):


    print()

    print("=" * 70)
    print("DISCOVERY - PRINTER ASSISTANT")
    print("=" * 70)

    print()

    print(
        "Escaneando rede..."
    )


    ips = scan_rede(base)


    print()

    print(
        f"{len(ips)} hosts ativos encontrados."
    )


    encontrados = []


    print()

    print(
        "Testando PJL..."
    )


    tarefas = []


    for ip in ips:

        tarefas.append(
            testar_pjl(ip)
        )


    resultados = await asyncio.gather(
        *tarefas
    )


    for device in resultados:

        if device:

            encontrados.append(
                device
            )


    print()

    print(
        f"{len(encontrados)} impressora(s) encontrada(s)."
    )


    return encontrados



# ============================================================
# TESTE PJL
# ============================================================

async def testar_pjl(ip):


    device = PrinterDevice(
        ip
    )


    try:


        await asyncio.wait_for(

            asyncio.to_thread(
                device.coletar_pjl
            ),

            timeout=TIMEOUT_PJL

        )


    except asyncio.TimeoutError:


        print(
            f"[PJL TIMEOUT] {ip}"
        )

        return None



    except Exception as erro:


        print(
            f"[PJL ERRO] {ip}: {erro}"
        )

        return None



    ident = device.identificacao


    modelo = ident.get(
        "modelo",
        "Desconhecido"
    )


    serial = ident.get(
        "serial",
        "Desconhecido"
    )


    fabricante = ident.get(
        "fabricante",
        "Desconhecido"
    )


    if (

        modelo != "Desconhecido"

        or

        serial != "Desconhecido"

        or

        fabricante != "Desconhecido"

    ):


        return device



    return None