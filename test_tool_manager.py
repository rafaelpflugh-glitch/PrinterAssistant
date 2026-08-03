from core.app_registry import criar_registry
from core.tool_manager import ToolManager
from core.session import criar_sessao



print("="*60)

print("TESTE TOOL MANAGER")

print("="*60)



registry = criar_registry()



manager = ToolManager(
    registry
)



print()

print("FERRAMENTAS:")


for ferramenta in manager.listar():

    print(
        ferramenta
    )



print()

print("EXECUTANDO PJL PAGECOUNT")



sessao = criar_sessao()

sessao.carregar()



resultado = manager.executar(

    "pjl",

    sessao,

    "pagecount"

)



print()

print(resultado)