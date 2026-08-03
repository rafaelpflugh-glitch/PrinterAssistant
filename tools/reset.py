from core.tool import Tool


class ResetTool(Tool):

    name = "reset"

    description = "Executa resets"

    category = "Reset"

    def run(self, action=None, **kwargs):

        print()

        print("Reset Tool")

        print()

        print("Reset:", action)

        return True