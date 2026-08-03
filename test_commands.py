from core.session import criar_sessao
from modules.commands import PrinterCommands

sessao = criar_sessao()

if not sessao.carregar():

    print("Nenhuma sessão.")

    quit()

cmd = PrinterCommands(sessao)

print()

print("="*70)
print("STATUS")
print("="*70)

print(
    cmd.status()
)

print()

print("="*70)
print("PAGECOUNT")
print("="*70)

print(
    cmd.pagecount()
)

print()

print("="*70)
print("MEMORY")
print("="*70)

print(
    cmd.memory()
)