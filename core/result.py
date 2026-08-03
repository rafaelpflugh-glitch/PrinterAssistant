# ============================================================
# PRINTER ASSISTANT
# TOOL RESULT
# ============================================================

class ToolResult:


    MAX_PREVIEW = 500


    def __init__(
        self,
        tool,
        action,
        resultado=None,
        sucesso=True,
        mensagem="",
        debug=None
    ):

        self.sucesso = sucesso

        self.tool = tool

        self.action = action

        self.resultado = resultado

        self.mensagem = mensagem

        self.debug = debug



    # ========================================================
    # LIMPA RESULTADOS GRANDES
    # ========================================================

    def _limitar_resultado(self):

        if self.resultado is None:
            return None


        if isinstance(self.resultado, str):

            if len(self.resultado) > self.MAX_PREVIEW:

                return (
                    self.resultado[:self.MAX_PREVIEW]
                    +
                    "\n...[TRUNCADO]"
                )


        return self.resultado



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

                self._limitar_resultado(),


            "debug":

                self.debug


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