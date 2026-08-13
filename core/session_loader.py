"""
Printer Assistant

Session Loader

Carrega uma identidade de impressora
dentro da sessão ativa.
"""


from fingerprint.fingerprint import Fingerprint

from profiles.loader import ProfileLoader



class SessionLoader:


    @staticmethod
    def load(

        session,

        fingerprint

    ):


        if isinstance(

            fingerprint,

            Fingerprint

        ):

            dados = fingerprint.to_dict()

        else:

            dados = fingerprint



        #
        # IDENTIDADE
        #

        session.model = dados.get("model")

        session.serial = dados.get("serial")

        session.firmware = dados.get("firmware")

        session.memory = dados.get("memory")

        session.pagecount = dados.get("pagecount")

        session.vendor = dados.get("vendor")



        session.fingerprint = dados



        #
        # PROFILE
        #

        session.profile = ProfileLoader.load(

            session.model

        )



        session.capabilities = session.profile.get(

            "capabilities",

            []

        )


        session.supported_commands = session.profile.get(

            "supported_commands",

            []

        )



        return session