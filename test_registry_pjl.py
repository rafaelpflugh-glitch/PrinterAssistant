from core.session import PrinterSession
from tools.pjl_tool import PJLTool


print("="*60)
print("TESTE REGISTRY PJL")
print("="*60)


sessao = PrinterSession()


if not sessao.carregar():

    print(
        "Nenhuma sessão."
    )

    exit()



tool = PJLTool(
    sessao
)


print()

print("PAGECOUNT:")
print("-"*60)


resultado = tool.execute(
    "pagecount"
)


print(
    resultado
)