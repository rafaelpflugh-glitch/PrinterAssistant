"""
============================================================
Printer Assistant
Scanner Tool
============================================================
"""

import asyncio

from core.base_tool import BaseTool
from core.result import ToolResult

from core.scanner import scan
from core.session_loader import SessionLoader


class ScannerTool(BaseTool):

    name = "scanner"

    description = "Scanner de Impressoras"

    category = "Rede"

    icon = "network"

    def __init__(self):

        super().__init__()

    # -----------------------------------------------------

    def execute(

        self,

        session,

        action=None,

        base="192.168.14",

        **kwargs

    ):

        try:

            #
            # procura impressoras
            #

            encontrados = asyncio.run(

                scan(base)

            )

            if not encontrados:

                return ToolResult.erro(

                    self.name,

                    "scan",

                    "Nenhuma impressora encontrada."

                ).to_dict()

            #
            # primeira encontrada
            #

            ip = encontrados[0]["ip"]

            SessionLoader.load(

                session,

                ip

            )

            return ToolResult(

                tool=self.name,

                action="scan",

                resultado=session.info(),

                sucesso=True

            ).to_dict()

        except Exception as erro:

            return ToolResult.erro(

                self.name,

                "scan",

                str(erro)

            ).to_dict()