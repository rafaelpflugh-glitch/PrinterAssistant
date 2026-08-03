from core.base_tool import BaseTool

from core.result import ToolResult


class ResetTool(BaseTool):

    name = "reset"

    description = "Executa resets"

    category = "Reset"

    actions = {

        "maintenance":{

            "description":"Reset manutenção"

        },

        "network":{

            "description":"Reset rede"

        },

        "apps":{

            "description":"Reset Apps"

        },

        "erase_memory":{

            "description":"Apagar memória"

        }

    }

    def execute(self, session, action=None, **kwargs):

        return ToolResult(

            self.name,

            action,

            {

                "reset":action,

                "executado":True

            }

        ).to_dict()