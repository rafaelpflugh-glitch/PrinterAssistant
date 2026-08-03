from core.tool_manager import ToolManager


class Executor:

    def __init__(self, session):

        self.manager = ToolManager(session)

    def execute(

        self,

        tool,

        action,

        **kwargs

    ):

        return self.manager.execute(

            tool,

            action,

            **kwargs

        )