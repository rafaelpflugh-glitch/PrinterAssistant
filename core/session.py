import json
from pathlib import Path
from datetime import datetime


# ============================================================
# PRINTER ASSISTANT - SESSION
# ============================================================
#
# Mantém a impressora atualmente selecionada pelo técnico.
#
# O scanner descobre.
# O técnico seleciona.
# A sessão guarda.
# Os próximos módulos usam.
#
# Assim não precisamos pedir o IP novamente em:
#
#   diagnóstico
#   ativo
#   etiqueta
#   página de teste
#   histórico
#   RMA
#   garantia
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

SESSION_FILE = BASE_DIR / "session.json"


# ============================================================
# CLASSE DA SESSÃO
# ============================================================

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
    # ATIVAR PELO DEVICE
    # ========================================================

    def ativar(self, device):

        agora = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        dados = device.to_dict()


        self.ativa = True


        if self.criada_em is None:

            self.criada_em = agora


        self.atualizada_em = agora


        self.ip = dados.get(
            "ip"
        )


        self.nome = dados.get(
            "nome"
        )


        self.identificacao = dados.get(

            "identificacao",

            self.identificacao

        )


        self.conectividade = dados.get(

            "conectividade",

            self.conectividade

        )


        self.supplies = dados.get(

            "supplies",

            []

        )


        self.estado = dados.get(

            "estado",

            "OFFLINE"

        )


        self.total_supplies = len(
            self.supplies
        )


        self.salvar()


        return self


    # ========================================================
    # DESATIVAR
    # ========================================================

    def desativar(self):

        self.ativa = False

        self.ip = None

        self.nome = None

        self.supplies = []

        self.estado = "OFFLINE"

        self.total_supplies = 0


        self.salvar()


    # ========================================================
    # SALVAR
    # ========================================================

    def salvar(self):

        dados = {

            "sessao": {

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

                dados = json.load(
                    arquivo
                )


            sessao = dados.get(
                "sessao",
                {}
            )


            self.ativa = bool(
                sessao.get(
                    "ativa",
                    False
                )
            )


            self.criada_em = sessao.get(
                "criada_em"
            )


            self.atualizada_em = sessao.get(
                "atualizada_em"
            )


            self.ip = sessao.get(
                "ip"
            )


            self.nome = sessao.get(
                "nome"
            )


            self.identificacao = sessao.get(

                "identificacao",

                self.identificacao

            )


            self.conectividade = sessao.get(

                "conectividade",

                self.conectividade

            )


            self.supplies = sessao.get(

                "supplies",

                []

            )


            self.estado = sessao.get(

                "estado",

                "OFFLINE"

            )


            self.total_supplies = len(
                self.supplies
            )


            return True


        except Exception as erro:

            print(
                f"[SESSION] Erro ao carregar: {erro}"
            )

            return False


    # ========================================================
    # EXISTE SESSÃO?
    # ========================================================

    def existe(self):

        return (

            self.ativa

            and

            self.ip is not None

        )


    # ========================================================
    # RESUMO
    # ========================================================

    def resumo(self):

        if not self.existe():

            return {

                "ativa": False,

                "mensagem":
                    "Nenhuma impressora selecionada."

            }


        return {

            "ativa": True,

            "ip": self.ip,

            "fabricante":
                self.identificacao.get(
                    "fabricante"
                ),

            "modelo":
                self.identificacao.get(
                    "modelo"
                ),

            "familia":
                self.identificacao.get(
                    "familia"
                ),

            "tipo":
                self.identificacao.get(
                    "tipo"
                ),

            "serial":
                self.identificacao.get(
                    "serial"
                ),

            "contador":
                self.identificacao.get(
                    "contador"
                ),

            "estado":
                self.estado,

            "supplies":
                self.total_supplies

        }


    # ========================================================
    # SERIAL
    # ========================================================

    def serial(self):

        return self.identificacao.get(
            "serial"
        )


    # ========================================================
    # MODELO
    # ========================================================

    def modelo(self):

        return self.identificacao.get(
            "modelo"
        )


    # ========================================================
    # FABRICANTE
    # ========================================================

    def fabricante(self):

        return self.identificacao.get(
            "fabricante"
        )


    # ========================================================
    # CONTADOR
    # ========================================================

    def contador(self):

        return self.identificacao.get(
            "contador"
        )


    # ========================================================
    # REPRESENTAÇÃO
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


# ============================================================
# FUNÇÃO DE CONVENIÊNCIA
# ============================================================

def criar_sessao():

    return PrinterSession()


# ============================================================
# TESTE DIRETO
# ============================================================

def teste():

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE SESSION"
    )

    print("=" * 60)


    print()

    sessao = PrinterSession()


    if not sessao.carregar():

        print(
            "Nenhuma sessão existente."
        )

        print()

        print(
            "Isso é normal se for o primeiro uso."
        )

        print()

        return


    if not sessao.existe():

        print(
            "Não existe uma impressora ativa."
        )

        print()

        return


    resumo = sessao.resumo()


    print()

    print(
        "IMPRESSORA ATIVA"
    )

    print(
        "-" * 60
    )


    print(
        "Fabricante:",
        resumo["fabricante"]
    )


    print(
        "Modelo:",
        resumo["modelo"]
    )


    print(
        "Família:",
        resumo["familia"]
    )


    print(
        "Tipo:",
        resumo["tipo"]
    )


    print(
        "Serial:",
        resumo["serial"]
    )


    contador = resumo["contador"]


    if contador is None:

        print(
            "Contador: desconhecido"
        )

    else:

        print(

            "Contador:",

            f"{contador:,}".replace(
                ",",
                "."
            )

        )


    print()

    print(
        "Estado:",
        resumo["estado"]
    )


    print(
        "Suprimentos:",
        resumo["supplies"]
    )


    print()

    print(
        "IP interno:",
        resumo["ip"]
    )


    print()

    print(
        "Sessão carregada com sucesso."
    )


    print()

    print(
        "Arquivo:"
    )


    print(
        SESSION_FILE
    )


    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    teste()