"""
Printer Assistant
Fingerprint Parser

Monta um Fingerprint a partir das respostas PJL.
"""

from fingerprint.fingerprint import Fingerprint

from parsers.pjl_parser import PJLParser


class FingerprintParser:

    @classmethod
    def build(

        cls,

        model_text=None,

        prodinfo_text=None,

        memory_text=None,

        pagecount_text=None

    ):

        model = None
        serial = None
        firmware = None
        memory = None
        pagecount = None

        #
        # MODEL
        #

        if model_text:

            model = PJLParser.info_id(model_text)

        #
        # PRODINFO
        #

        if prodinfo_text:

            info = PJLParser.prodinfo(prodinfo_text)

            serial = (

                info.get("serial")

                or info.get("serialnumber")

                or info.get("printer_serial")

            )

            firmware = (

                info.get("firmware")

                or info.get("fwversion")

                or info.get("version")

            )

        #
        # MEMORY
        #

        if memory_text:

            memoria = PJLParser.memory(memory_text)

            memory = (

                memoria.get("total_memory")

                or memoria.get("memory")

            )

        #
        # PAGECOUNT
        #

        if pagecount_text:

            pagecount = PJLParser.pagecount(pagecount_text)

        #
        # Vendor
        #

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