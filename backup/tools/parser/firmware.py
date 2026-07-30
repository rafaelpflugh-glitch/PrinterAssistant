import re


def extrair_firmware(texto, secoes):

    firmware = None

    if "RIP Firmware Version" in secoes:

        linhas = secoes["RIP Firmware Version"].splitlines()

        for linha in linhas:

            linha = linha.strip()

            if linha.startswith("LW"):

                firmware = linha

                break

    if firmware is None:

        resultado = re.search(

            r"RIP Firmware Version.*?\n(.*?)\n",

            texto,

            re.DOTALL

        )

        if resultado:

            firmware = resultado.group(1).strip()

    return {

        "rip": firmware

    }