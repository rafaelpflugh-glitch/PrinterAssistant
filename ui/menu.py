from tools.scanner import descobrir_impressoras
from core.session import Session



class Menu:


    def __init__(self):

        self.impressoras = []

        self.session = Session()



    def executar(self):


        while True:


            self.cabecalho()


            print("1 - Procurar impressoras")

            print("2 - Selecionar impressora")

            print("3 - Informações")

            print("4 - Comandos")

            print("5 - Rotinas")

            print("6 - Banco de dados")

            print("0 - Sair")


            print()


            op = input("> ")



            if op == "1":

                self.scan()



            elif op == "2":

                self.selecionar()



            elif op == "3":

                self.info()



            elif op == "0":

                break




    def cabecalho(self):


        print()

        print("="*45)

        print(" HERMES ASSISTENTE DE BANCADA")

        print("="*45)


        if self.session.ativa():

            print()

            print("IMPRESSORA ATUAL")

            print("----------------")

            print(
                self.session.mostrar()
            )


        else:

            print()

            print(
                "Nenhuma impressora conectada"
            )


        print()




    def scan(self):


        rede = input(
            "Rede (ex: 192.168.14): "
        )


        self.impressoras = descobrir_impressoras(
            rede
        )




    def selecionar(self):


        if not self.impressoras:

            print(
                "Faça uma busca primeiro"
            )

            return



        print()


        for i,p in enumerate(self.impressoras):

            print(
                i+1,
                "-",
                p.ip
            )



        escolha = int(
            input("> ")
        )


        printer = self.impressoras[
            escolha-1
        ]


        self.session.conectar(
            printer
        )


        print(
            "Impressora conectada!"
        )




    def info(self):


        if not self.session.ativa():

            print(
                "Nenhuma impressora"
            )

            return


        print()

        print(
            self.session.mostrar()
        )