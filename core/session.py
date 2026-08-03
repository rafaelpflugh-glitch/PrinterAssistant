import json
from pathlib import Path
from datetime import datetime


# ============================================================
# PRINTER ASSISTANT - SESSION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SESSION_FILE = BASE_DIR / "session.json"



class PrinterSession:


    def __init__(self):

        self.ativa = False

        self.criada_em = None

        self.atualizada_em = None

        self.ip = None

        self.nome = None


        self.identificacao = {

            "fabricante": "Desconhecido",
            "modelo": "Desconhecido",
            "familia": "",
            "tipo": "",
            "serial": "Desconhecido",
            "contador": None

        }


        self.conectividade = {

            "ip": None,
            "snmp": False,
            "pjl": False,
            "web": False,
            "raw": False,
            "ipp": False

        }


        self.supplies = []

        self.estado = "OFFLINE"

        self.total_supplies = 0



    # ========================================================
    # ATIVAR
    # ========================================================

    def ativar(self, device):


        agora = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        dados = device.to_dict()


        if not self.ativa:

            self.criada_em = agora



        self.ativa = True

        self.atualizada_em = agora


        self.ip = dados.get("ip")

        self.nome = dados.get("nome")


        self.identificacao = dados.get(
            "identificacao",
            {}
        )


        self.conectividade = dados.get(
            "conectividade",
            {}
        )


        self.supplies = dados.get(
            "supplies",
            []
        )


        self.estado = dados.get(
            "estado",
            "DESCONHECIDO"
        )


        self.total_supplies = len(
            self.supplies
        )


        self.salvar()


        return self



    # ========================================================
    # SALVAR
    # ========================================================

    def salvar(self):


        dados = {

            "sessao": self.to_dict()

        }


        with open(

            SESSION_FILE,

            "w",

            encoding="utf-8"

        ) as arquivo:


            json.dump(

                dados,

                arquivo,

                indent=4,

                ensure_ascii=False

            )



    # ========================================================
    # CARREGAR
    # ========================================================

    def carregar(self):


        if not SESSION_FILE.exists():

            return False



        try:

            with open(

                SESSION_FILE,

                "r",

                encoding="utf-8"

            ) as arquivo:

                dados=json.load(
                    arquivo
                )


            sessao=dados.get(
                "sessao",
                {}
            )


            self.__dict__.update(
                sessao
            )


            return True



        except Exception as erro:


            print(
                "[SESSION]",
                erro
            )

            return False



    # ========================================================
    # EXISTE
    # ========================================================

    def existe(self):

        return (

            self.ativa

            and

            self.ip is not None

        )



    # ========================================================
    # LIMPAR
    # ========================================================

    def desativar(self):


        self.ativa=False

        self.ip=None

        self.supplies=[]

        self.estado="OFFLINE"

        self.total_supplies=0


        self.salvar()



    # ========================================================
    # DADOS
    # ========================================================

    def to_dict(self):

        return {


            "ativa":
                self.ativa,


            "criada_em":
                self.criada_em,


            "atualizada_em":
                self.atualizada_em,


            "ip":
                self.ip,


            "nome":
                self.nome,


            "identificacao":
                self.identificacao,


            "conectividade":
                self.conectividade,


            "supplies":
                self.supplies,


            "estado":
                self.estado,


            "total_supplies":
                self.total_supplies

        }



    # ========================================================
    # HELPERS
    # ========================================================


    def fabricante(self):

        return self.identificacao.get(
            "fabricante"
        )



    def modelo(self):

        return self.identificacao.get(
            "modelo"
        )



    def serial(self):

        return self.identificacao.get(
            "serial"
        )



    def contador(self):

        return self.identificacao.get(
            "contador"
        )



    # ========================================================
    # MOSTRAR
    # ========================================================

    def mostrar(self):


        if not self.existe():

            print(
                "Nenhuma impressora ativa."
            )

            return



        print()

        print("="*70)
        print("IMPRESSORA ATUAL")
        print("="*70)


        print()

        print(
            "Fabricante:",
            self.fabricante()
        )


        print(
            "Modelo:",
            self.modelo()
        )


        print(
            "Serial:",
            self.serial()
        )


        print(
            "Contador:",
            self.contador()
        )


        print(
            "IP:",
            self.ip
        )


        print(
            "Estado:",
            self.estado
        )


        print(
            "Suprimentos:",
            self.total_supplies
        )


        print("="*70)



def criar_sessao():

    return PrinterSession()