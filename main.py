from core.hermes import Hermes
from core.command_manager import CommandManager



hermes = Hermes()

commands = CommandManager()



while True:


    print()

    print("=================================")

    print(" HERMES ASSISTENTE DE BANCADA ")

    print("=================================")



    if hermes.ip:

        print(
            "Impressora:",
            hermes.ip
        )

    else:

        print(
            "Nenhuma impressora conectada"
        )


    print()

    print("1 - Conectar impressora")

    print("2 - Informações")

    print("3 - Comandos")

    print("0 - Sair")



    opcao = input("> ")




    if opcao == "1":


        ip = input(
            "IP da impressora: "
        )


        hermes.conectar(ip)




    elif opcao == "2":


        hermes.informacoes()




    elif opcao == "3":


        if not hermes.ip:

            print(
                "Nenhuma impressora conectada"
            )

            continue




        marca = "Lexmark"



        lista = commands.listar(
            marca
        )



        if not lista:

            print(
                "Nenhum comando cadastrado"
            )

            continue




        print()

        print("==============================")

        print("COMANDOS")

        print("==============================")




        for i, comando in enumerate(lista,1):


            print(

                i,
                "-",
                comando.get("nome"),
                "|",
                comando.get("tipo","geral"),
                "| risco:",
                comando.get("risco","baixo")

            )





        escolha = input(
            "\nEscolha: "
        )



        try:


            selecionado = lista[
                int(escolha)-1
            ]


            hermes.executar_comando(

                marca,

                selecionado["nome"]

            )


        except Exception as erro:


            print(
                "Erro:",
                erro
            )




    elif opcao == "0":


        break