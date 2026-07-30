from tools.network import testar
from tools.printer import coletar_debug
from tools.ews import explorar
from tools.parser.suprimentos import extrair_suprimentos

from core.contexto import atualizar

import re


# ==================================================
# UTILITÁRIOS
# ==================================================

def extrair_campo(padrao, texto):

    resultado = re.search(
        padrao,
        texto,
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )

    if resultado:
        return resultado.group(1).strip()

    return "Não encontrado"


# ==================================================
# DIAGNÓSTICO
# ==================================================

def diagnosticar(ip):

    resultado = []

    serial = None
    firmware = None
    suprimentos = None
    dados = ""

    resultado.append("""
=================================

      DIAGNÓSTICO LEXMARK

=================================
""")

    resultado.append(f"IP ANALISADO:\n{ip}\n")

    # ==================================
    # REDE
    # ==================================

    try:

        rede = testar(ip)

        resultado.append(f"""
[REDE]

{rede}

""")

    except Exception as erro:

        resultado.append(f"\n[ERRO REDE]\n{erro}\n")

    # ==================================
    # EWS
    # ==================================

    try:

        resultado.append(explorar(ip))

    except Exception as erro:

        resultado.append(f"\n[ERRO EWS]\n{erro}\n")

    # ==================================
    # SYSDEBUG
    # ==================================

    try:

        dados = coletar_debug(ip)

        if not dados:

            resultado.append("\n[ERRO] SysDebugData vazio.\n")

        elif "Printer Serial Number" not in dados:

            resultado.append("\n[ERRO] SysDebugData inválido.\n")

        else:

            serial = extrair_campo(
                r"Printer Serial Number:\s*(\S+)",
                dados
            )

            firmware = extrair_campo(
                r"RIP Firmware Version.*?\n(.*?)\n",
                dados
            )

            resultado.append(f"""
=================================

IDENTIFICAÇÃO

Serial:
{serial}

Firmware:
{firmware}

SysDebugData:
OK

=================================
""")

            suprimentos = extrair_suprimentos(dados)

            resultado.append(f"""
SUPRIMENTOS

UNIDADE DE IMAGEM

Serial:
{suprimentos['unidade_serial']}

Páginas:
{suprimentos['unidade_paginas']}

Nível:
{suprimentos['unidade_nivel']}%


TONER PRETO

Serial:
{suprimentos['toner_serial']}

ID CHIP:
{suprimentos['toner_chip']}

Páginas:
{suprimentos['toner_paginas']}

Restante:
{suprimentos['toner_restante']}

Capacidade:
{suprimentos['toner_capacidade']}

Nível:
{suprimentos['toner_nivel']}%
""")

    except Exception as erro:

        resultado.append(f"\n[ERRO DEBUG]\n{erro}\n")

    resultado.append("""
=================================

DIAGNÓSTICO FINALIZADO

=================================
""")

    resultado_final = "\n".join(resultado)

    # ==================================
    # ATUALIZA CONTEXTO
    # ==================================

    atualizar({

        "ip": ip,

        "serial": serial,

        "firmware": firmware,

        "ultimo_debug": dados,

        "ultimo_diagnostico": resultado_final,

        "suprimentos": suprimentos

    })

    return resultado_final