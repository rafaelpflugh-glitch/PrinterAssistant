from tools.scanner import descobrir_impressoras
from core.session import Session


class Menu:

    def __init__(self):

        self.impressoras = []

        self.session = Session()

    # ==========================================================
    # LOOP PRINCIPAL
    # ==========================================================

    def executar(self):

        while True:

            self.cabecalho()

            print("1 - Descobrir impressoras")
            print("2 - Selecionar impressora")
            print("3 - Painel da impressora")

            print()

            print("===== RELATÓRIOS =====")
            print("4 - Relatório de Ativo")
            print("5 - Garantia")
            print("6 - RMA")

            print()

            print("===== SERVIÇO =====")
            print("7 - Comandos PJL")
            print("8 - Rotinas Técnicas")
            print("9 - Firmware")
            print("10 - Banco de Dados")

            print()

            print("0 - Sair")

            print()

            op = input("> ").strip()

            if op == "1":

                self.scan()

            elif op == "2":

                self.selecionar()

            elif op == "3":

                self.info()

            elif op == "4":

                self.relatorio_ativo()

            elif op == "5":

                print("\nGarantia (em desenvolvimento)\n")

            elif op == "6":

                print("\nRMA (em desenvolvimento)\n")

            elif op == "7":

                print("\nComandos PJL (em desenvolvimento)\n")

            elif op == "8":

                print("\nRotinas Técnicas (em desenvolvimento)\n")

            elif op == "9":

                print("\nFirmware (em desenvolvimento)\n")

            elif op == "10":

                print("\nBanco de Dados (em desenvolvimento)\n")

            elif op == "0":

                break

    # ==========================================================
    # CABEÇALHO
    # ==========================================================

    def cabecalho(self):

        print()
        print("=" * 60)
        print("PRINTER ASSISTANT")
        print("=" * 60)

        if self.session.ativa():

            print()

            print("IMPRESSORA ATUAL")
            print("-" * 60)

            print(self.session.mostrar())

        else:

            print()
            print("Nenhuma impressora selecionada.")

        print()

    # ==========================================================
    # DESCOBERTA
    # ==========================================================

    def scan(self):

        rede = input(
            "Rede (ex: 192.168.14): "
        ).strip()

        self.impressoras = descobrir_impressoras(rede)

    # ==========================================================
    # SELEÇÃO
    # ==========================================================

    def selecionar(self):

        if not self.impressoras:

            print("\nPrimeiro execute uma descoberta.\n")

            return

        print()

        for i, p in enumerate(self.impressoras, 1):

            modelo = getattr(p, "modelo", lambda: "Desconhecido")()

            print(f"{i} - {modelo} ({p.ip})")

        print()

        try:

            escolha = int(input("> "))

            printer = self.impressoras[escolha - 1]

        except Exception:

            print("\nEscolha inválida.\n")

            return

        self.session.conectar(printer)

        print("\nImpressora conectada.\n")

    # ==========================================================
    # PAINEL
    # ==========================================================

    def info(self):

        if not self.session.ativa():

            print("\nNenhuma impressora conectada.\n")

            return

        print()
        print(self.session.mostrar())

    # ==========================================================
    # RELATÓRIO DE ATIVO
    # ==========================================================

    def relatorio_ativo(self):

        if not self.session.ativa():

            print("\nNenhuma impressora conectada.\n")

            return

        from reports.ativo import RelatorioAtivo

        relatorio = RelatorioAtivo()

        relatorio.imprimir(self.session.device)

        print("\nRelatório de Ativo enviado para a TSC.\n")