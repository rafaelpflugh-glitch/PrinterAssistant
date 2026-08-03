from core.result import ToolResult


class Validator:

    def __init__(self, session):

        self.session = session

    def validate(self):

        if not self.session.existe():

            return ToolResult.error(

                tool="system",

                action="validation",

                mensagem="Nenhuma impressora ativa."

            )

        return None