"""
Printer Assistant
PJL Actions Layer

Camada de alto nível para comandos PJL.

Não envia comandos diretamente pelo sistema.
Usa a sessão atual da impressora.

"""

from modules.pjl import PJL



class PJLActions:


    def __init__(self, session):

        self.session = session

        self.pjl = PJL(session)



    # =====================================================
    # INFORMAÇÕES
    # =====================================================

    def status(self):

        return self.pjl.status()



    def pagecount(self):

        return self.pjl.pagecount()



    def memory(self):

        return self.pjl.memory()



    def info_id(self):

        return self.pjl.info_id()



    def prodinfo(self):

        return self.pjl.prodinfo()



    # =====================================================
    # DISPLAY
    # =====================================================

    def mostrar_mensagem(self, texto):

        """
        Exibe mensagem no painel da impressora
        """

        return self.pjl.display(texto)



    def limpar_display(self):

        """
        Retorna display ao padrão
        """

        return self.pjl.display(
            ""
        )



    def display_pronto(self):

        return self.pjl.display(
            "Pronto"
        )



    # =====================================================
    # SISTEMA
    # =====================================================

    def reset(self):

        return self.pjl.reset()



    def initialize(self):

        return self.pjl.initialize()



    # =====================================================
    # TESTE
    # =====================================================

    def pagina_teste(self):

        return self.pjl.testpage()



    # =====================================================
    # EXECUÇÃO GENÉRICA
    # =====================================================

    def executar(self, comando):

        return self.pjl.raw(
            comando
        )