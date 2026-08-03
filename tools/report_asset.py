from core.tool import Tool

from reports.ativo import imprimir_relatorio


def executar(session, **kwargs):

    imprimir_relatorio(session)


tool = Tool(

    id="report_asset",

    name="Relatório de Ativo",

    description="Imprime etiqueta patrimonial.",

    category="Relatórios",

    manufacturer=None,

    family=None,

    models=[],

    requires_session=True,

    callback=executar

)