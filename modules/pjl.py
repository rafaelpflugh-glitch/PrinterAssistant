from pjl.client import PJLClient
from pjl import commands



class PJL:


    def __init__(self, session):

        self.session = session

        self.client = PJLClient(
            session.ip
        )



    # ======================================================
    # ENVIO BASE
    # ======================================================

    def raw(self, command):

        return self.client.send(
            command
        )



    # ======================================================
    # IDENTIFICAÇÃO
    # ======================================================

    def info_id(self):

        return self.raw(
            commands.INFO_ID
        )



    def prodinfo(self):

        return self.raw(
            commands.INFO_PRODINFO
        )



    def serial(self):

        resposta = self.info_id()


        for linha in resposta.splitlines():

            linha = linha.strip()


            if linha.startswith('"'):

                return (
                    linha
                    .replace('"',"")
                )


        return resposta.strip()



    # ======================================================
    # STATUS
    # ======================================================

    def status(self):

        return self.raw(
            commands.INFO_STATUS
        )



    def pagecount(self):

        return self.raw(
            commands.INFO_PAGECOUNT
        )



    def memory(self):

        return self.raw(
            commands.INFO_MEMORY
        )



    def config(self):

        return self.raw(
            commands.INFO_CONFIG
        )



    def variables(self):

        return self.raw(
            commands.INFO_VARIABLES
        )



    # ======================================================
    # FILESYSTEM
    # ======================================================

    def filesystem(self):

        return self.raw(
            commands.INFO_FILESYS
        )



    def fsdir(self):

        return self.raw(
            commands.FSDIRLIST
        )



    def fsquery(self):

        return self.raw(
            commands.FSQUERY
        )



    def fsinit(self):

        return self.raw(
            commands.FSINIT
        )



    # ======================================================
    # DISPLAY
    # ======================================================

    def display(self,texto):

        return self.raw(
            commands.READY_MESSAGE(texto)
        )



    def clear_display(self):

        return self.raw(
            commands.CLEAR_DISPLAY()
        )



    # ======================================================
    # SISTEMA
    # ======================================================

    def reset(self):

        return self.raw(
            commands.RESET
        )



    def initialize(self):

        return self.raw(
            commands.INITIALIZE
        )



    def defaults(self):

        return self.raw(
            commands.DEFAULTS
        )



    # ======================================================
    # PÁGINAS
    # ======================================================

    def testpage(self):

        return self.raw(
            commands.TESTPAGE
        )



    def config_page(self):

        return self.raw(
            commands.CONFIG_PAGE
        )



    def supplies_page(self):

        return self.raw(
            commands.SUPPLIES_PAGE
        )



    def diagnostic_page(self):

        return self.raw(
            commands.DIAGNOSTIC_PAGE
        )