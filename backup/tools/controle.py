from tools.ews_actions import (
    reset_fabrica,
    reset_rede,
    reset_apps,
    apagar_memoria
)



def executar_acao(tipo,ip):


    print(
f"""
=================================

AÇÃO SOLICITADA

Impressora:
{ip}

Comando:
{tipo}

=================================
"""
    )



    confirmar = input(
        "Confirmar execução? (s/n): "
    )



    if confirmar.lower() != "s":


        return "Cancelado pelo técnico."



    if tipo == "fabrica":


        ok,msg = reset_fabrica(ip)



    elif tipo == "rede":


        ok,msg = reset_rede(ip)



    elif tipo == "apps":


        ok,msg = reset_apps(ip)



    elif tipo == "memoria":


        ok,msg = apagar_memoria(ip)



    else:


        return "Ação desconhecida."




    if ok:


        return """

=================================

Comando enviado com sucesso.

A impressora pode reiniciar
ou perder comunicação.

=================================

"""


    else:


        return f"""

Falha:

{msg}

""" 