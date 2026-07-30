from core.printer_profile import PrinterProfile
from core.command_executor import CommandExecutor


class Hermes:


    def __init__(self):

        self.impressora = None
        self.ip = None




    def conectar(self, ip):


        self.ip = ip

        self.impressora = PrinterProfile(ip)


        print()

        print("==============================")

        print("IMPRESSORA CONECTADA")

        print("==============================")

        print(ip)





    def informacoes(self):


        if not self.impressora:

            print(
                "Nenhuma impressora conectada"
            )

            return



        dados = self.impressora.carregar()


        if not dados:


            print(
                "Sem perfil salvo"
            )

            return



        print()

        print("==============================")

        print("INFORMAÇÕES")

        print("==============================")



        for chave, valor in dados.items():

            print(
                chave,
                ":",
                valor
            )





    def executar_comando(
        self,
        marca,
        comando
    ):


        if not self.ip:

            print(
                "Nenhuma impressora conectada"
            )

            return



        executor = CommandExecutor(

            self.ip

        )


        resultado = executor.executar(

            marca,

            comando

        )


        print()

        print(resultado)