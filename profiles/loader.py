"""
Printer Assistant
Profile Loader

Responsável por identificar o profile
correto da impressora.
"""

from profiles.lexmark.ms610 import MS610Profile
from profiles.lexmark.mx511 import MX511Profile
from profiles.lexmark.mx611 import MX611Profile


class ProfileLoader:


    def __init__(self):

        self.profiles = [

            MS610Profile(),

            MX511Profile(),

            MX611Profile()

        ]


    # =====================================================
    # DETECÇÃO
    # =====================================================

    def detect(

        self,

        model

    ):

        if not model:

            return None


        model = model.lower()


        for profile in self.profiles:


            if profile.match(model):

                return profile


        return None



    # =====================================================
    # COMPATIBILIDADE
    # =====================================================

    @classmethod
    def load(

        cls,

        model

    ):

        """

        Atalho utilizado pelo sistema.

        Permite:

        ProfileLoader.load("Lexmark MS610")

        """

        loader = cls()


        profile = loader.detect(

            model

        )


        if profile is None:

            return {

                "family": "Unknown",

                "capabilities": [],

                "supported_commands": []

            }


        return {

            "family":

                profile.family,


            "capabilities":

                profile.capabilities,


            "supported_commands":

                profile.supported_commands,


            "default_port":

                profile.default_port

        }