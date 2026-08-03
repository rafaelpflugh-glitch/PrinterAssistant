from core.base_tool import BaseTool

from core.result import ToolResult


class FirmwareTool(BaseTool):

    name="firmware"

    description="Firmware"

    category="Firmware"

    actions={

        "install":{

            "description":"Instalar"

        },

        "backup":{

            "description":"Backup"

        },

        "downgrade":{

            "description":"Downgrade"

        }

    }

    def execute(self,session,action=None,**kwargs):

        return ToolResult(

            self.name,

            action,

            {

                "acao":action,

                "executado":True

            }

        ).to_dict()