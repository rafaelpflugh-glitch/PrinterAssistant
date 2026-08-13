"""
Perfil base Lexmark
"""


class LexmarkProfile:

    model = ""

    family = ""

    capabilities = []

    supported_commands = []

    default_port = 9100

    # ------------------------------------------------

    def match(self, model):

        if not model:
            return False

        return self.model.lower() in model.lower()

    # ------------------------------------------------

    def info(self):

        return {

            "model": self.model,

            "family": self.family,

            "capabilities": self.capabilities,

            "supported_commands": self.supported_commands,

            "default_port": self.default_port

        }