from core.tool import Tool


class FirmwareTool(Tool):

    name = "firmware"

    description = "Operações de firmware"

    category = "Firmware"

    def run(self, action=None, **kwargs):

        print()

        print("Firmware Tool")

        print()

        print("Ação:", action)

        return True