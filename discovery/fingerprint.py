"""
Printer Assistant

Fingerprint

Responsável por gerar uma assinatura da impressora
a partir das respostas PJL.
"""


class Fingerprint:

    def __init__(self):

        self.data = {}

    # -------------------------------------------------

    def add(self, key, value):

        if value is None:
            return

        self.data[key] = value

    # -------------------------------------------------

    def merge(self, dictionary):

        if not dictionary:
            return

        for key, value in dictionary.items():

            if value is None:
                continue

            self.data[key] = value

    # -------------------------------------------------

    def manufacturer(self):

        model = self.data.get("model", "")

        if not model:
            return None

        first = model.split()[0]

        return first

    # -------------------------------------------------

    def model(self):

        return self.data.get("model")

    # -------------------------------------------------

    def serial(self):

        return self.data.get("serial")

    # -------------------------------------------------

    def firmware(self):

        return self.data.get("firmware")

    # -------------------------------------------------

    def memory(self):

        return self.data.get("memory")

    # -------------------------------------------------

    def pagecount(self):

        return self.data.get("pagecount")

    # -------------------------------------------------

    def to_dict(self):

        return dict(self.data)

    # -------------------------------------------------

    def __repr__(self):

        return f"Fingerprint({self.data})"