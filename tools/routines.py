from tools.executor import Executor


class Rotinas:

    def __init__(self, ip):

        self.exec = Executor(ip)


    def pagina_teste(self):

        print()

        print("=== PAGINA DE TESTE ===")

        self.exec.abrir(
            "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html"
        )


    def configuracao(self):

        print()

        print("=== CONFIGURAÇÃO ===")

        self.exec.abrir(
            "/cgi-bin/dynamic/printer/config/reports/MenusPage.html"
        )


    def estatisticas(self):

        print()

        print("=== ESTATÍSTICAS ===")

        self.exec.abrir(
            "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html"
        )