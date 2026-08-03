from core.session import criar_sessao
from tools.pjl_tool import PJLTool


sessao = criar_sessao()

sessao.carregar()


tool = PJLTool()


resultado = tool.execute(
    sessao,
    action="pagecount"
)


print(resultado)