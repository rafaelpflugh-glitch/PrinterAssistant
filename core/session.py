"""
Printer Assistant
Session

Representa a impressora atualmente conectada.

Existe apenas UMA sessão ativa.
"""


from fingerprint.fingerprint import Fingerprint

from profiles.loader import ProfileLoader



class Session:


    def __init__(self):

        self.clear()



    # =====================================================
    # RESET
    # =====================================================


    def clear(self):

        self.connected = False


        self.ip = None

        self.port = 9100

        self.socket = None



        #
        # Identificação
        #

        self.model = None

        self.serial = None

        self.firmware = None

        self.memory = None

        self.pagecount = None

        self.vendor = None



        #
        # Inteligência
        #

        self.fingerprint = None

        self.profile = None

        self.capabilities = []

        self.supported_commands = []



    # =====================================================
    # STATUS
    # =====================================================


    def exists(self):

        return self.connected



    # =====================================================
    # CONEXÃO
    # =====================================================


    def connect(

        self,

        ip,

        socket=None,

        port=9100

    ):

        self.connected = True

        self.ip = ip

        self.socket = socket

        self.port = port



    def disconnect(self):

        self.clear()



    # =====================================================
    # FINGERPRINT
    # =====================================================


    def update_from_parser(

        self,

        parsed

    ):

        """
        Atualiza sessão através do Fingerprint.
        """


        if isinstance(

            parsed,

            Fingerprint

        ):

            parsed = parsed.to_dict()



        self.model = parsed.get("model")

        self.serial = parsed.get("serial")

        self.firmware = parsed.get("firmware")

        self.memory = parsed.get("memory")

        self.pagecount = parsed.get("pagecount")

        self.vendor = parsed.get("vendor")



        self.fingerprint = parsed



        #
        # Carrega perfil automaticamente
        #

        self.profile = ProfileLoader.load(

            self.model

        )



        self.capabilities = self.profile.get(

            "capabilities",

            []

        )


        self.supported_commands = self.profile.get(

            "supported_commands",

            []

        )



    # =====================================================
    # CAPACIDADES
    # =====================================================


    def has(

        self,

        capability

    ):

        return capability in self.capabilities



    # =====================================================
    # COMANDOS
    # =====================================================


    def supports(

        self,

        command

    ):

        """

        Verifica se a impressora suporta
        determinado comando.

        """

        return command in self.supported_commands



    # =====================================================
    # PROFILE
    # =====================================================


    def family(self):

        if not self.profile:

            return None


        return self.profile.get(

            "family"

        )



    # =====================================================
    # DEBUG
    # =====================================================


    def info(self):

        return {


            "connected":

                self.connected,


            "ip":

                self.ip,


            "port":

                self.port,


            "model":

                self.model,


            "serial":

                self.serial,


            "firmware":

                self.firmware,


            "memory":

                self.memory,


            "pagecount":

                self.pagecount,


            "vendor":

                self.vendor,


            "family":

                self.family(),


            "profile":

                self.profile,


            "capabilities":

                self.capabilities,


            "supported_commands":

                self.supported_commands


        }