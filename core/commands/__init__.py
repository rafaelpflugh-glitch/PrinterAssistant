"""
============================================================
PRINTER ASSISTANT
COMMANDS
============================================================

Camada de comandos de alto nível.

Responsável por:

    - carregar database/commands.json;
    - localizar comandos pelo nome;
    - encaminhar comandos para o Executor;
    - expor os comandos disponíveis.

Não contém lógica HTTP.
Não contém lógica PJL.
Não contém lógica de hardware.

A execução real é feita pelo Executor.
============================================================
"""

from __future__ import annotations

import json
from pathlib import Path

from core.executor import Executor


class Commands:

    """
    Gerenciador de comandos definidos em database/commands.json.
    """

    # ========================================================
    # CONSTRUTOR
    # ========================================================

    def __init__(self, printer):

        self.printer = printer

        self.executor = Executor(
            printer
        )

        self.db = self._carregar()

    # ========================================================
    # DATABASE
    # ========================================================

    @staticmethod
    def _caminho_database():

        # core/commands/__init__.py
        #
        # parents[0] = core/commands
        # parents[1] = core
        # parents[2] = PrinterAssistant

        raiz = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        return (
            raiz
            / "database"
            / "commands.json"
        )

    def _carregar(self):

        arquivo = self._caminho_database()

        if not arquivo.exists():

            raise FileNotFoundError(
                "Arquivo de comandos não encontrado: "
                f"{arquivo}"
            )

        with arquivo.open(
            "r",
            encoding="utf-8"
        ) as f:

            dados = json.load(f)

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
    # CONSULTA
    # ========================================================

    def listar(self):

        return list(
            self.db.keys()
        )

    def existe(
        self,
        nome
    ):

        return (
            str(nome).strip()
            in self.db
        )

    def obter(
        self,
        nome
    ):

        nome = str(
            nome
        ).strip()

        return self.db.get(
            nome
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

        if not nome:

            return {
                "success": False,
                "tool": "commands",
                "action": None,
                "error": (
                    "Nome do comando não informado."
                )
            }

        if nome not in self.db:

            return {
                "success": False,
                "tool": "commands",
                "action": nome,
                "error": (
                    f"Comando '{nome}' "
                    "não encontrado."
                )
            }

        comando = self.db[nome]

        if not isinstance(
            comando,
            dict
        ):

            return {
                "success": False,
                "tool": "commands",
                "action": nome,
                "error": (
                    f"Definição do comando "
                    f"'{nome}' inválida."
                )
            }

        metodo = str(
            comando.get(
                "method",
                "GET"
            )
        ).upper().strip()

        endpoint = comando.get(
            "endpoint"
        )

        if not endpoint:

            return {
                "success": False,
                "tool": "commands",
                "action": nome,
                "error": (
                    f"Comando '{nome}' "
                    "não possui endpoint."
                )
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
        # MÉTODO NÃO SUPORTADO
        # ----------------------------------------------------

        return {
            "success": False,
            "tool": "commands",
            "action": nome,
            "error": (
                f"Método HTTP '{metodo}' "
                f"não suportado pelo comando "
                f"'{nome}'."
            )
        }

    # ========================================================
    # DEBUG
    # ========================================================

    def info(self):

        return {
            "commands": self.listar(),
            "database": str(
                self._caminho_database()
            )
        }