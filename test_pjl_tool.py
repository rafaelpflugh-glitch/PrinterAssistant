from core.session import criar_sessao
from modules.pjl import PJL


print("="*60)
print("TESTE PJL")
print("="*60)


sessao = criar_sessao()


if not sessao.carregar():

    print()
    print("Nenhuma sessão encontrada.")
    print("Execute main.py primeiro.")
    exit()


print()

sessao.mostrar()


print()

print("Criando módulo PJL...")


pjl = PJL(
    sessao
)


print()

print("PAGECOUNT")
print("-"*60)

resultado = pjl.pagecount()

print(resultado)