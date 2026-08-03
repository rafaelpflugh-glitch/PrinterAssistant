from core.session import criar_sessao

from modules.pjl_actions import PJLActions


sessao = criar_sessao()

if not sessao.carregar():

    print("Nenhuma sessão.")

    quit()


pjl = PJLActions(sessao)


while True:

    print()

    print("="*60)

    print("PJL ACTIONS")

    print("="*60)

    print()

    print("1 Status")

    print("2 Page Count")

    print("3 Memory")

    print("4 Mostrar mensagem")

    print("5 Test Page")

    print("6 Initialize")

    print("7 Reset")

    print("0 Sair")

    print()

    op = input("> ")


    if op == "0":

        break


    elif op == "1":

        print(

            pjl.status()

        )


    elif op == "2":

        print(

            pjl.pagecount()

        )


    elif op == "3":

        print(

            pjl.memory()

        )


    elif op == "4":

        texto = input(

            "Mensagem: "

        )

        print(

            pjl.display(texto)

        )


    elif op == "5":

        print(

            pjl.test_page()

        )


    elif op == "6":

        print(

            pjl.initialize()

        )


    elif op == "7":

        print(

            pjl.reset()

        )