from pathlib import Path


class LexmarkProfile:

    fabricante = "Lexmark"

    protocolo = "PJL"

    usa_snmp = True

    usa_pjl = True

    usa_web = True

    usa_raw = True

    firmware_dir = Path("firmware") / "lexmark"

    reset_dir = Path("reset") / "lexmark"

    report_padrao = "ativo"

    garantia = True

    historico = True

    workflows = [
        "diagnostico",
        "preparar_venda",
        "rma",
        "revisao"
    ]

    def info(self):

        return {

            "fabricante": self.fabricante,

            "protocolo": self.protocolo,

            "snmp": self.usa_snmp,

            "pjl": self.usa_pjl,

            "web": self.usa_web,

            "raw": self.usa_raw,

            "firmware_dir": str(self.firmware_dir),

            "reset_dir": str(self.reset_dir),

            "workflow": self.workflows

        }