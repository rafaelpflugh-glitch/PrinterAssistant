class Session:


    def __init__(self):

        self.printer = None



    def conectar(self, printer):

        self.printer = printer



    def desconectar(self):

        self.printer = None



    def ativa(self):

        return self.printer is not None



    def mostrar(self):

        if not self.printer:

            return "Nenhuma impressora selecionada"


        texto = []

        texto.append(
            f"Modelo: {self.printer.modelo or 'Desconhecido'}"
        )

        texto.append(
            f"IP: {self.printer.ip}"
        )


        texto.append(
            f"Serial: {self.printer.serial or 'Não lido'}"
        )


        return "\n".join(texto)