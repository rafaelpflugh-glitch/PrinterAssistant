"""
Printer Assistant
PJL Tool

Ferramenta responsável pelos comandos PJL.
"""

from core.base_tool import BaseTool
from core.result import ToolResult
from core.action import Action

from modules.pjl import PJL
from parsers.pjl_parser import PJLParser


class PJLTool(BaseTool):

    name = "pjl"
    description = "Comandos PJL"
    category = "Impressora"
    icon = "terminal"

    def __init__(self):

        super().__init__()

        # =====================================================
        # REGISTRO DAS AÇÕES
        # =====================================================

        self.register_action(

            Action(
                name="id",
                description="Modelo",
                executor=lambda pjl: pjl.info_id(),
                parser=lambda texto: {
                    "model": PJLParser.info_id(texto)
                }
            )

        )

        self.register_action(

            Action(
                name="prodinfo",
                description="Informações do produto",
                executor=lambda pjl: pjl.prodinfo(),
                parser=PJLParser.prodinfo
            )

        )

        self.register_action(

            Action(
                name="pagecount",
                description="Contador de páginas",
                executor=lambda pjl: pjl.pagecount(),
                parser=lambda texto: {
                    "pagecount": PJLParser.pagecount(texto)
                }
            )

        )

        self.register_action(

            Action(
                name="status",
                description="Status",
                executor=lambda pjl: pjl.status(),
                parser=PJLParser.status
            )

        )

        self.register_action(

            Action(
                name="memory",
                description="Memória",
                executor=lambda pjl: pjl.memory(),
                parser=PJLParser.memory
            )

        )

        self.register_action(

            Action(
                name="config",
                description="Configuração",
                executor=lambda pjl: pjl.config(),
                parser=PJLParser.config
            )

        )

        self.register_action(

            Action(
                name="variables",
                description="Variáveis",
                executor=lambda pjl: pjl.variables(),
                parser=PJLParser.variables
            )

        )

    # =====================================================
    # EXECUÇÃO
    # =====================================================

    def execute(

        self,
        session,
        action="status",
        **kwargs

    ):

        try:

            acao = self.get_action(action)

            if acao is None:

                return ToolResult.erro(

                    tool=self.name,
                    action=action,
                    mensagem=f"Ação '{action}' inexistente."

                ).to_dict()

            #
            # Contexto PJL
            #

            pjl = PJL(session)

            resultado = acao.run(pjl)

            return ToolResult(

                tool=self.name,
                action=action,
                resultado=resultado,
                sucesso=True

            ).to_dict()

        except Exception as erro:

            return ToolResult.erro(

                tool=self.name,
                action=action,
                mensagem=str(erro)

            ).to_dict()