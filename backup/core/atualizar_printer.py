from tools.printer import coletar_debug

from tools.parser2 import parse

from core.contexto import atualizar


def atualizar_printer(ip):

    dados = coletar_debug(ip)

    printer = parse(dados)

    printer["rede"]["ip"] = ip

    atualizar({

        "printer": printer,

        "ultimo_debug": dados

    })

    return printer