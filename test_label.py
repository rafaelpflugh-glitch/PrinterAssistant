import asyncio

from modules.discovery import descobrir
from modules.inventory import inventariar_lista

from labels.active_label import ActiveLabel


async def main():

    lista = await descobrir("192.168.14")

    await inventariar_lista(lista)

    impressora = lista[0]

    etiqueta = ActiveLabel(impressora)

    print(etiqueta.zpl())

    etiqueta.imprimir()

    print("Etiqueta enviada.")


asyncio.run(main())