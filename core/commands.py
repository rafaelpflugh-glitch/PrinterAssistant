"""
============================================================
PRINTER ASSISTANT
COMMANDS
============================================================

Carrega comandos definidos em:

    database/commands.json

e encaminha a execução para o Executor.

Exemplo de comando:

{
    "printer_status": {
        "method": "GET",
        "endpoint": "/cgi-bin/dynamic/printer/PrinterStatus.html"
    }
}

Esta camada NÃO conhece a lógica HTTP/PJL.
Ela apenas:

    1. carrega o comando;
    2. identifica o método;
    3. identifica o endpoint;
    4. encaminha para o Executor.
============================================================
"""

from __future__ import annotations

import json
from pathlib import Path

from core.executor import Executor


class Commands:

    # ========================================================
    # CONSTRUTOR
    # ========================================================

    def __init__(self, printer):

        self.printer = printer

        self.executor = Executor(
            printer
        )

        # ----------------------------------------------------
        # Localização do projeto
        # ----------------------------------------------------

        self.project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        self.database_file = (
            self.project_root
            / "database"
            / "commands.json"
        )

        self.db = self._carregar()

    # ========================================================
    # CARREGAMENTO
    # ========================================================

    def _carregar(self):

        if not self.database_file.exists():

            raise FileNotFoundError(
                "Arquivo de comandos não encontrado: "
                f"{self.database_file}"
            )

        with open(
            self.database_file,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(
                arquivo
            )

        if not isinstance(
            dados,
            dict
        ):

            raise ValueError(
                "database/commands.json "
                "deve conter um objeto JSON."
            )

        return dados

    # ========================================================
    # CONSULTAS
    # ========================================================

    def existe(
        self,
        nome
    ):

        return nome in self.db

    def obter(
        self,
        nome
    ):

        return self.db.get(
            nome
        )

    def listar(self):

        return list(
            self.db.keys()
        )

    # ========================================================
    # EXECUÇÃO
    # ========================================================

    def executar(
        self,
        nome
    ):

        nome = str(
            nome
        ).strip()

        # ----------------------------------------------------
        # Verifica comando
        # ----------------------------------------------------

        if nome not in self.db:

            return {

                "success": False,

                "tool": "commands",

                "action": nome,

                "error":
                    f"Comando '{nome}' não existe "
                    "em database/commands.json."

            }

        # ----------------------------------------------------
        # Obtém definição
        # ----------------------------------------------------

        cmd = self.db[nome]

        if not isinstance(
            cmd,
            dict
        ):

            return {

                "success": False,

                "tool": "commands",

                "action": nome,

                "error":
                    f"Definição do comando '{nome}' "
                    "é inválida."

            }

        metodo = str(
            cmd.get(
                "method",
                ""
            )
        ).strip().upper()

        endpoint = cmd.get(
            "endpoint"
        )

        # ----------------------------------------------------
        # Validação
        # ----------------------------------------------------

        if not metodo:

            return {

                "success": False,

                "tool": "commands",

                "action": nome,

                "error":
                    f"Comando '{nome}' não possui "
                    "method definido."

            }

        if not endpoint:

            return {

                "success": False,

                "tool": "commands",

                "action": nome,

                "error":
                    f"Comando '{nome}' não possui "
                    "endpoint definido."

            }

        # ----------------------------------------------------
        # GET
        # ----------------------------------------------------

        if metodo == "GET":

            return self.executor.get(
                endpoint
            )

        # ----------------------------------------------------
        # POST
        # ----------------------------------------------------

        if metodo == "POST":

            return self.executor.post(
                endpoint
            )

        # ----------------------------------------------------
        # Método desconhecido
        # ----------------------------------------------------

        return {

            "success": False,

            "tool": "commands",

            "action": nome,

            "error":
                f"Método HTTP '{metodo}' "
                f"não suportado para '{nome}'."

        }