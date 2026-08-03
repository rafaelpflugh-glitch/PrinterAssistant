import json
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent


class FirmwareRepository:

    def __init__(self):

        self.base = BASE / "firmware"

    def _database(self, fabricante, modelo):

        return (
            self.base
            / fabricante.lower()
            / modelo.lower()
            / "firmware.json"
        )

    def carregar(self, fabricante, modelo):

        arquivo = self._database(
            fabricante,
            modelo
        )

        if not arquivo.exists():
            return None

        with open(
            arquivo,
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def listar(self, fabricante, modelo):

        banco = self.carregar(
            fabricante,
            modelo
        )

        if banco is None:
            return []

        return banco.get(
            "firmwares",
            []
        )

    def localizar(
        self,
        fabricante,
        modelo,
        versao
    ):

        for fw in self.listar(
            fabricante,
            modelo
        ):

            if fw["versao"] == versao:

                return fw

        return None

    def ultimo(
        self,
        fabricante,
        modelo
    ):

        lista = self.listar(
            fabricante,
            modelo
        )

        if not lista:
            return None

        return lista[-1]

    def primeiro(
        self,
        fabricante,
        modelo
    ):

        lista = self.listar(
            fabricante,
            modelo
        )

        if not lista:
            return None

        return lista[0]