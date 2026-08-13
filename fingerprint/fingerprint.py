"""
Printer Assistant
Fingerprint

Objeto que representa a identidade completa da impressora.

Ele será preenchido pelos parsers.
"""


class Fingerprint:

    def __init__(

        self,

        model=None,

        serial=None,

        firmware=None,

        memory=None,

        pagecount=None,

        vendor=None

    ):

        self.model = model

        self.serial = serial

        self.firmware = firmware

        self.memory = memory

        self.pagecount = pagecount

        self.vendor = vendor

    # -----------------------------------------------------

    def to_dict(self):

        return {

            "model": self.model,

            "serial": self.serial,

            "firmware": self.firmware,

            "memory": self.memory,

            "pagecount": self.pagecount,

            "vendor": self.vendor

        }

    # -----------------------------------------------------

    @classmethod

    def from_dict(

        cls,

        data

    ):

        return cls(

            model=data.get("model"),

            serial=data.get("serial"),

            firmware=data.get("firmware"),

            memory=data.get("memory"),

            pagecount=data.get("pagecount"),

            vendor=data.get("vendor")

        )

    # -----------------------------------------------------

    def __repr__(self):

        return (

            f"Fingerprint("

            f"model={self.model}, "

            f"serial={self.serial}, "

            f"firmware={self.firmware}, "

            f"memory={self.memory}, "

            f"pagecount={self.pagecount}, "

            f"vendor={self.vendor}"

            f")"

        )