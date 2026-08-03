from modules.pjl import PJL



class PJLCapabilities:


    def __init__(self, session):

        self.session = session

        self.pjl = PJL(session)



    def testar(self):

        resultado = {}


        # ==========================================
        # CONSULTAS
        # ==========================================

        consultas = {


            "info_id":
                self.pjl.info_id,


            "status":
                self.pjl.status,


            "pagecount":
                self.pjl.pagecount,


            "memory":
                self.pjl.memory

        }



        for nome, funcao in consultas.items():


            try:

                resposta = funcao()


                resultado[nome] = bool(
                    resposta
                )


            except Exception as erro:


                resultado[nome] = False




        # ==========================================
        # AÇÕES
        # ==========================================

        acoes = {


            "display":

                lambda:
                self.pjl.display(
                    "PJL TEST"
                )


        }



        for nome, funcao in acoes.items():


            try:

                funcao()


                resultado[nome] = True


            except Exception:


                resultado[nome] = False



        return resultado