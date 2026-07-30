import requests



# ==================================================
# PÁGINA DE DEMONSTRAÇÃO
# ==================================================

def pagina_demonstracao(ip):

    try:

        url = f"http://{ip}/cgi-bin/demopage"


        resposta = requests.get(
            url,
            timeout=5
        )


        if resposta.status_code == 200:

            return "Página de demonstração solicitada."


        return f"Falha ao solicitar página. HTTP {resposta.status_code}"


    except Exception as erro:

        return f"Erro enviando página de demonstração:\n{erro}"





# ==================================================
# RELATÓRIO DE ATIVOS
# ==================================================

def relatorio_ativo(ip):

    try:

        url = f"http://{ip}/cgi-bin/assetreport"


        resposta = requests.get(
            url,
            timeout=5
        )


        if resposta.status_code == 200:

            return "Relatório de ativos solicitado."


        return f"Falha ao solicitar relatório. HTTP {resposta.status_code}"


    except Exception as erro:

        return f"Erro enviando relatório de ativos:\n{erro}"





# ==================================================
# PÁGINA DE CONFIGURAÇÃO
# ==================================================

def pagina_configuracao(ip):

    try:

        url = f"http://{ip}/cgi-bin/configpage"


        resposta = requests.get(
            url,
            timeout=5
        )


        if resposta.status_code == 200:

            return "Página de configuração solicitada."


        return f"Falha ao solicitar configuração. HTTP {resposta.status_code}"


    except Exception as erro:

        return f"Erro enviando configuração:\n{erro}"





# ==================================================
# PAPEL PESADO
# ==================================================

def configurar_papel_pesado(ip):

    try:

        url = f"http://{ip}/cgi-bin/setconfig"


        dados = {

            "paper_weight": "heavy"

        }


        resposta = requests.post(
            url,
            data=dados,
            timeout=5
        )


        if resposta.status_code == 200:

            return "Configuração papel pesado enviada."


        return f"Falha configurando papel. HTTP {resposta.status_code}"


    except Exception as erro:

        return f"Erro configurando papel pesado:\n{erro}"





# ==================================================
# TEXTURA ÁSPERA
# ==================================================

def configurar_textura_aspero(ip):

    try:

        url = f"http://{ip}/cgi-bin/setconfig"


        dados = {

            "paper_texture": "rough"

        }


        resposta = requests.post(
            url,
            data=dados,
            timeout=5
        )


        if resposta.status_code == 200:

            return "Configuração textura áspera enviada."


        return f"Falha configurando textura. HTTP {resposta.status_code}"


    except Exception as erro:

        return f"Erro configurando textura áspera:\n{erro}"