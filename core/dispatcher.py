class Dispatcher:

    def __init__(self, registry):

        self.registry = registry

    # -----------------------

    def execute(

        self,

        tool_id,

        session,

        **kwargs

    ):

        tool = self.registry.get(tool_id)

        if tool is None:

            raise Exception(

                f"Ferramenta inexistente: {tool_id}"

            )

        if tool.requires_session:

            if session is None:

                raise Exception(

                    "Sessão obrigatória."

                )

        return tool.callback(

            session,

            **kwargs

        )