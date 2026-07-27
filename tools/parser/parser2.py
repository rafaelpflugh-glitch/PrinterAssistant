import re

from core.printer import nova


def campo(padrao, texto):

    r = re.search(

        padrao,

        texto,

        re.IGNORECASE | re.MULTILINE | re.DOTALL

    )

    if r:

        return r.group(1).strip()

    return None


def parse(dados):

    printer = nova()

    printer["identificacao"]["serial"] = campo(
        r"Printer Serial Number:\s*(\S+)",
        dados
    )

    printer["identificacao"]["firmware"] = campo(
        r"RIP Firmware Version.*?\n(.*?)\n",
        dados
    )

    printer["rede"]["ip"] = None

    return printer