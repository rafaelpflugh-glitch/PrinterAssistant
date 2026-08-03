from modules.pjl_actions import PJLActions
from modules.pjl_parser import PJLParser
from core.session import criar_sessao



sessao = criar_sessao()

sessao.carregar()


pjl = PJLActions(sessao)


print("="*60)
print("PARSER PJL")
print("="*60)


print()

raw = pjl.pagecount()

print("RAW:")
print(raw)


print()

print("PARSED:")

print(
    PJLParser.pagecount(raw)
)
