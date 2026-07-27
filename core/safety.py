class Safety:


    @staticmethod
    def confirmar(comando):


        risco = comando.get(
            "risco",
            "baixo"
        )


        if risco == "baixo":

            return True



        print()

        print("==============================")

        print("ATENÇÃO")

        print("==============================")

        print(
            "Comando:",
            comando["nome"]
        )

        print(
            "Risco:",
            risco
        )


        resposta = input(
            "Deseja continuar? S/N: "
        )


        return resposta.lower() == "s"