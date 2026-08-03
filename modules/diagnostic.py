from core.session import PrinterSession



# ============================================================
# PRINTER ASSISTANT
# DIAGNOSTIC ENGINE
# ============================================================


class PrinterDiagnostic:


    def __init__(self, session):

        self.session = session

        self.resultado = {

            "rede": None,

            "pjl": None,

            "snmp": None,

            "raw": None,

            "estado": None,

            "alertas": []

        }



    # ========================================================
    # EXECUTAR
    # ========================================================

    def executar(self):


        if not self.session.existe():

            self.resultado["estado"] = (
                "SEM IMPRESSORA"
            )

            return self.resultado



        self.verificar_conectividade()

        self.analisar_supplies()

        self.gerar_estado()


        return self.resultado




    # ========================================================
    # CONECTIVIDADE
    # ========================================================

    def verificar_conectividade(self):


        conexao = self.session.conectividade



        self.resultado["rede"] = True


        self.resultado["pjl"] = (
            conexao.get(
                "pjl",
                False
            )
        )


        self.resultado["snmp"] = (
            conexao.get(
                "snmp",
                False
            )
        )


        self.resultado["raw"] = (
            conexao.get(
                "raw",
                False
            )
        )



        if not self.resultado["pjl"]:

            self.resultado["alertas"].append(
                "PJL indisponível"
            )



        if not self.resultado["snmp"]:

            self.resultado["alertas"].append(
                "SNMP indisponível"
            )




    # ========================================================
    # ANALISAR SUPRIMENTOS
    # ========================================================

    def analisar_supplies(self):


        for item in self.session.supplies:


            nivel = item.get(
                "nivel",
                0
            )


            nome = item.get(
                "nome",
                "Suprimento"
            )



            if nivel <= 30:


                self.resultado["alertas"].append(

                    f"{nome}: nível crítico ({nivel}%)"

                )



            elif nivel <= 60:


                self.resultado["alertas"].append(

                    f"{nome}: atenção ({nivel}%)"

                )




    # ========================================================
    # ESTADO FINAL
    # ========================================================

    def gerar_estado(self):


        alertas = len(
            self.resultado["alertas"]
        )


        if alertas == 0:


            self.resultado["estado"] = (
                "EXCELENTE"
            )


        elif alertas <= 2:


            self.resultado["estado"] = (
                "ATENÇÃO"
            )


        else:


            self.resultado["estado"] = (
                "CRÍTICO"
            )





# ============================================================
# FUNÇÃO SIMPLES
# ============================================================

def diagnosticar(session):


    motor = PrinterDiagnostic(
        session
    )


    return motor.executar()