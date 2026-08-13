"""
Printer Assistant - PJL Identity

Consulta informações básicas da impressora através de PJL.
O IP é apenas o endereço atual da impressora.
Não é usado como identidade permanente.
"""

import re


class PJLIdentity:
    def __init__(self, writer):
        self.writer = writer

    def _query(self, comando):
        resposta = self.writer.enviar(comando)
        return resposta.strip()

    def info(self):
        """
        Tenta obter informações de identidade disponíveis via PJL INFO.
        """

        resultado = {
            "model": None,
            "serial": None,
            "firmware": None,
            "raw": {},
        }

        consultas = {
            "id": "@PJL INFO ID",
            "config": "@PJL INFO CONFIG",
            "status": "@PJL INFO STATUS",
        }

        for nome, comando in consultas.items():
            try:
                resposta = self._query(comando)
            except Exception as exc:
                resultado["raw"][nome] = f"ERROR: {exc}"
                continue

            resultado["raw"][nome] = resposta

            self._extrair_identidade(
                resposta,
                resultado,
            )

        return resultado

    @staticmethod
    def _extrair_identidade(texto, resultado):
        if not texto:
            return

        padroes = {
            "model": [
                r"MODEL\s*=\s*(.+)",
                r"MODELNAME\s*=\s*(.+)",
                r"PRODUCTNAME\s*=\s*(.+)",
            ],
            "serial": [
                r"SERIAL\s*=\s*(.+)",
                r"SERIALNUMBER\s*=\s*(.+)",
            ],
            "firmware": [
                r"FIRMWARE\s*=\s*(.+)",
                r"FIRMWAREVERSION\s*=\s*(.+)",
                r"FWVERSION\s*=\s*(.+)",
            ],
        }

        for campo, lista in padroes.items():
            if resultado[campo] is not None:
                continue

            for padrao in lista:
                encontrado = re.search(
                    padrao,
                    texto,
                    flags=re.IGNORECASE,
                )

                if encontrado:
                    valor = encontrado.group(1).strip()
                    resultado[campo] = valor
                    break