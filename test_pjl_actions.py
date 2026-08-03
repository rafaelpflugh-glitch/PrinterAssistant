from core.session import criar_sessao
from modules.pjl import PJL

sessao = criar_sessao()

if not sessao.carregar():

    print("Nenhuma sessão.")

    quit()

pjl = PJL(sessao)

print("="*60)
print("PRODINFO")
print("="*60)

print(pjl.prodinfo())

print()

print("="*60)
print("FILESYSTEM")
print("="*60)

print(pjl.fsdir())

print()

print("="*60)
print("DISPLAY")
print("="*60)

print(
    pjl.display("Printer Assistant")
)