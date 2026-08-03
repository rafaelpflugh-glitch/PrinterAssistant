from modules.pjl_actions import PJLActions
from core.session import criar_sessao



print("="*60)
print("TESTE PJL ACTIONS")
print("="*60)



sessao = criar_sessao()


if not sessao.carregar():

    print(
        "Nenhuma sessão encontrada."
    )

    exit()



if not sessao.existe():

    print(
        "Nenhuma impressora ativa."
    )

    exit()



pjl = PJLActions(
    sessao
)



print()

print(
    "IMPRESSORA:"
)

print(
    sessao.modelo()
)


print()

print(
    "PAGECOUNT"
)

print(
    pjl.pagecount()
)


print()

print(
    "DISPLAY TESTE"
)

print(
    pjl.mostrar_mensagem(
        "PRINTER ASSISTANT"
    )
)


print()

print(
    "OK"
)