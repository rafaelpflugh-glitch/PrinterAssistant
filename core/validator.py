from core.result import ToolResult


class Validator:

    """
    Faz somente validações.

    Não executa nada.
    """

    def __init__(self, session):

        self.session = session

    # ======================================================

    def validate(self, intent):

        # ------------------------
        # sessão
        # ------------------------

        if not self.session.existe():

            return ToolResult.erro(

                tool="system",

                action="validation",

                mensagem="Nenhuma impressora ativa."

            ).to_dict()

        # ------------------------
        # intent

        if intent is None:

            return ToolResult.erro(

                tool="system",

                action="intent",

                mensagem="Intent inválida."

            ).to_dict()

        if not intent.tool:

            return ToolResult.erro(

                tool="system",

                action="intent",

                mensagem="Tool ausente."

            ).to_dict()

        if not intent.action:

            return ToolResult.erro(

                tool="system",

                action="intent",

                mensagem="Action ausente."

            ).to_dict()

        return None