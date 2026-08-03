from core.base_tool import BaseTool
from modules.pjl import PJL


class PJLTool(BaseTool):


    name = "pjl"

    description = "Comandos PJL da impressora"

    category = "PJL"

    icon = "🖨️"



    def execute(self, session, action="pagecount", **kwargs):


        pjl = PJL(session)



        if action == "pagecount":

            return pjl.pagecount()



        elif action == "status":

            return pjl.status()



        elif action == "serial":

            return pjl.serial()



        elif action == "memory":

            return pjl.memory()



        elif action == "config":

            return pjl.config()



        else:

            return {
                "erro":
                f"Ação PJL desconhecida: {action}"
            }