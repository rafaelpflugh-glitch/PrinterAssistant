import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ARQUIVO = BASE_DIR / "printers_found.json"


def salvar(dispositivos):

    dados = []

    for device in dispositivos:

        dados.append({

            "ip": device.ip,

            "identificacao": device.identificacao,

            "estado": device.estado(),

            "conectividade": device.conectividade,

            "total_supplies": device.total_supplies()

        })

    with open(

        ARQUIVO,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            dados,

            f,

            indent=4,

            ensure_ascii=False

        )


def carregar():

    if not ARQUIVO.exists():

        return []

    with open(

        ARQUIVO,

        encoding="utf-8"

    ) as f:

        return json.load(f)