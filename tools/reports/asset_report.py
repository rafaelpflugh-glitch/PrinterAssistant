from core.tools.registry import Tool
from core.tools.registry import registry


def executar():

    print()

    print("Relatório de Ativo")

    print("Em desenvolvimento.")


registry.registrar(

    Tool(

        id="asset_report",

        nome="Relatório de Ativo",

        categoria="Relatórios",

        descricao="Imprime etiqueta de ativo.",

        callback=executar

    )

)