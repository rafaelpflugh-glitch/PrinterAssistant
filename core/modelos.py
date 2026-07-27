import json
import os


def carregar(modelo):

    arquivo = os.path.join(

        "database",

        "models",

        modelo.lower() + ".json"

    )

    if not os.path.exists(arquivo):

        return None

    with open(

        arquivo,

        encoding="utf8"

    ) as f:

        return json.load(f)