from core.result import ToolResult



print("="*60)

print("TESTE TOOL RESULT")

print("="*60)



resultado = ToolResult(

    tool="pjl",

    action="pagecount",

    resultado={

        "pagecount":137967

    }

)



print()



print(
    resultado.to_dict()
)



print()



erro = ToolResult.erro(

    "reset",

    "maintenance",

    "Impressora offline"

)



print(
    erro.to_dict()
)
