from core.base_tool import BaseTool
from core.result import ToolResult

from modules.pjl import PJL
from modules.pjl_parser import PJLParser


class PJLTool(BaseTool):

    name = "pjl"

    description = "Comandos PJL"

    category = "Impressora"

    icon = "terminal"

    actions = {

        "id": {
            "description": "Modelo"
        },

        "prodinfo": {
            "description": "Informações"
        },

        "pagecount": {
            "description": "Contador"
        },

        "status": {
            "description": "Status"
        },

        "memory": {
            "description": "Memória"
        },

        "config": {
            "description": "Configuração"
        },

        "variables": {
            "description": "Variáveis"
        }

    }

    def execute(self, session, action="status", **kwargs):

        try:

            pjl = PJL(session)

            comandos = {

                "id": pjl.info_id,

                "prodinfo": pjl.prodinfo,

                "pagecount": pjl.pagecount,

                "status": pjl.status,

                "memory": pjl.memory,

                "config": pjl.config,

                "variables": pjl.variables

            }

            if action not in comandos:

                return ToolResult.erro(

                    self.name,

                    action,

                    "Ação inexistente"

                ).to_dict()

            resposta = comandos[action]()

            resultado = resposta

            if action == "pagecount":

                resultado = {

                    "pagecount":

                    PJLParser.pagecount(resposta)

                }

            elif action == "status":

                resultado = PJLParser.status(resposta)

            return ToolResult(

                self.name,

                action,

                resultado

            ).to_dict()

        except Exception as e:

            return ToolResult.erro(

                self.name,

                action,

                str(e)

            ).to_dict()