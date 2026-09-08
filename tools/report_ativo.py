
from core.tool import Tool

from reports.ativo import imprimir_relatorio_ativo


class ReportAtivoTool(Tool):

    name = "report_ativo"

    description = "Imprime relatório de ativo"

    category = "Relatórios"

    def run(
        self,
        **kwargs,
    ):

        # ----------------------------------------------------
        # O PrinterDevice deve ser fornecido pelo chamador.
        # ----------------------------------------------------

        device = kwargs.get(
            "device"
        )

        if device is None:

            raise ValueError(
                "ReportAtivoTool: nenhum PrinterDevice "
                "foi fornecido."
            )

        return imprimir_relatorio_ativo(
            device
        )

