# ============================================================
# PRINTER ASSISTANT
# TOOL RESULT
# ============================================================
#
# Retorno padrão de todas as ferramentas.
#
# PJL
# RESET
# FIRMWARE
# REPORTS
# WORKFLOWS
#
# Todos devem retornar este formato.
#
# ============================================================


class ToolResult:


    def __init__(
        self,
        tool,
        action,
        resultado=None,
        sucesso=True,
        mensagem=""
    ):

        self.sucesso = sucesso

        self.tool = tool

        self.action = action

        self.resultado = resultado

        self.mensagem = mensagem



    # ========================================================
    # DICT
    # ========================================================

    def to_dict(self):

        return {


            "sucesso":

                self.sucesso,


            "tool":

                self.tool,


            "action":

                self.action,


            "mensagem":

                self.mensagem,


            "resultado":

                self.resultado


        }



    # ========================================================
    # ERRO
    # ========================================================

    @classmethod
    def erro(
        cls,
        tool,
        action,
        mensagem
    ):

        return cls(

            tool,

            action,

            resultado=None,

            sucesso=False,

            mensagem=mensagem

        )
