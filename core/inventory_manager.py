from modules.inventory import inventariar

import json

from pathlib import Path

ARQUIVO = Path("data/inventory.json")


async def executar(device):

    device = await inventariar(device)

    salvar(device)

    return device


def salvar(device):

    with open(

        ARQUIVO,

        "w",

        encoding="utf8"

    ) as f:

        json.dump(

            device.to_dict(),

            f,

            indent=4,

            ensure_ascii=False

        )