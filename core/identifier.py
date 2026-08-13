
"""
Printer Assistant

Printer Identifier

Identifica uma impressora real via PJL.
"""


from fingerprint.fingerprint import Fingerprint

from parsers.pjl_parser import PJLParser

from modules.pjl import PJL



class PrinterIdentifier:


    def __init__(self, session):

        self.session = session

        self.pjl = PJL(session)



    # =====================================================
    # IDENTIFICAÇÃO COMPLETA
    # =====================================================


    def identify(self):


        #
        # MODELO
        #

        id_raw = self.pjl.info_id()


        model = PJLParser.info_id(

            id_raw

        )


        #
        # PRODINFO
        #

        prod_raw = self.pjl.prodinfo()


        prod = PJLParser.prodinfo(

            prod_raw

        )



        #
        # MEMÓRIA
        #

        memory_raw = self.pjl.memory()


        memory = PJLParser.memory(

            memory_raw

        )



        #
        # CONTADOR
        #

        count_raw = self.pjl.pagecount()


        pagecount = PJLParser.pagecount(

            count_raw

        )



        #
        # EXTRAÇÃO
        #

        serial = (

            prod.get("serial")

            or prod.get("serialnumber")

        )


        firmware = (

            prod.get("firmware")

            or prod.get("version")

            or prod.get("fwversion")

        )



        vendor = None


        if model:

            vendor = model.split()[0]



        return Fingerprint(

            model=model,

            serial=serial,

            firmware=firmware,

            memory=memory,

            pagecount=pagecount,

            vendor=vendor

        )