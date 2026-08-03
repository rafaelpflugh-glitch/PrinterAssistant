from core.session import criar_sessao

from modules.pjl import PJL

from modules.pjl_parser import PJLParser

sessao = criar_sessao()

sessao.carregar()

pjl = PJL(sessao)

print()

print("=" * 60)
print("STATUS")
print("=" * 60)

status = PJLParser.parse_status(

    pjl.status()

)

print(status)

print()

print("=" * 60)
print("PAGECOUNT")
print("=" * 60)

contador = PJLParser.parse_pagecount(

    pjl.pagecount()

)

print(contador)

print()

print("=" * 60)
print("MEMORY")
print("=" * 60)

mem = PJLParser.parse_memory(

    pjl.memory()

)

print(mem)