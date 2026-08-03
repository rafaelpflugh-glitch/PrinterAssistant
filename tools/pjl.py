from core.base_tool import BaseTool

from modules.pjl import PJL



class PJLTool(BaseTool):


    name = "pjl"


    description = (
        "Comandos PJL da impressora "
        "como status, pagecount, memória "
        "e informações."
    )



    def execute(self, session, action="status"):


        if session is None:

            return {

                "erro":
                "Nenhuma impressora ativa."

            }



        pjl = PJL(session)



        # ==================================================
        # AÇÕES DISPONÍVEIS
        # ==================================================

        if action == "status":


            return pjl.status()



        elif action == "pagecount":


            return pjl.pagecount()



        elif action == "memory":


            return pjl.memory()



        elif action == "id":


            return pjl.info_id()



        elif action == "serial":


            return pjl.serial()



        elif action == "display":


            texto = "Printer Assistant"

            return pjl.display(
                texto
            )



        else:


            return {

                "erro":
                f"Ação PJL desconhecida: {action}"

            }