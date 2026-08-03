from core.tools.registry import Tool
from core.tools.registry import registry


def executar():

    print()

    print("Reset Maintenance")

    print("Em desenvolvimento.")


registry.registrar(

    Tool(

        id="maintenance",

        nome="Reset Maintenance",

        categoria="Reset",

        descricao="Reinicia contador de manutenção.",

        callback=executar

    )

)