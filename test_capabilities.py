from core.session import criar_sessao
from modules.pjl_capabilities import PJLCapabilities


sessao = criar_sessao()


if not sessao.carregar():

    print("Sem sessão")

    exit()


teste = PJLCapabilities(sessao)


resultado = teste.testar()


print()

print("="*60)

print("CAPACIDADES PJL")

print("="*60)


for item, valor in resultado.items():

    print(
        f"{item:15}: {valor}"
    )