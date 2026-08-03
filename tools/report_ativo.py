from core.tool import Tool

from reports.ativo import imprimir_relatorio_ativo


class ReportAtivoTool(Tool):

    name = "report_ativo"

    description = "Imprime relatório de ativo"

    category = "Relatórios"

    def run(self, **kwargs):

        return imprimir_relatorio_ativo()