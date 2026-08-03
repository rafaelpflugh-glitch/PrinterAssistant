from profiles.lexmark.common import LexmarkProfile


class MX611Profile(LexmarkProfile):

    modelo = "Lexmark MX611"

    familia = "MX"

    adf = True

    duplex = True

    display_touch = True

    scanner = True

    fax = True

    color = False

    firmware = [

        "LW80.SB2.P433",

        "LW80.SB2.P434",

        "LW80.SB2.P435"

    ]

    resets = [

        "maintenance",

        "adf",

        "printer_settings",

        "network",

        "apps",

        "erase_memory",

        "out_of_service"

    ]

    def info(self):

        dados = super().info()

        dados.update({

            "modelo": self.modelo,

            "familia": self.familia,

            "scanner": self.scanner,

            "fax": self.fax,

            "touch": self.display_touch,

            "firmwares": self.firmware,

            "resets": self.resets

        })

        return dados