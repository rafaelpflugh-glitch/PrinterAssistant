from core.hermes import analisar
from core.executor import executar_acao

from core.contexto import (
    obter_contexto,
    atualizar
)

from core.memoria import salvar
from core.relatorio import criar_relatorio

from tools.analise_tecnica import analisar_resultados


# ==================================================
# COMANDOS DIRETOS
# ==================================================

def comando_direto(mensagem):

    texto = mensagem.lower()

    comandos = {

        "procurar": [
            "procurar impressora",
            "procure impressora",
            "procurar impressoras",
            "procure impressoras",
            "buscar impressora"
        ],

        "pagina_configuracao": [
            "pagina de configuração",
            "página de configuração",
            "imprima uma página de configuração"
        ],

        "pagina_demonstracao": [
            "pagina de demonstração",
            "página de demonstração"
        ],

        "relatorio_ativo": [
            "relatório ativo",
            "relatorio ativo"
        ],

        "papel_pesado": [
            "papel pesado"
        ],

        "textura_aspera": [
            "textura áspera",
            "textura aspera"
        ]

    }

    for acao, palavras in comandos.items():

        for palavra in palavras:

            if palavra in texto:

                return acao

    return None


# ==================================================
# EXTRAI ACAO DO HERMES
# ==================================================

def extrair_acao(texto):

    if not texto:
        return None

    if "ACAO:" not in texto:
        return None

    return (
        texto
        .split("ACAO:", 1)[1]
        .strip()
        .splitlines()[0]
        .replace("`", "")
        .strip()
    )


# ==================================================
# EXECUTOR PRINCIPAL
# ==================================================

def executar(mensagem):

    acao = comando_direto(mensagem)

    if not acao:

        resposta = analisar(mensagem)

        acao = extrair_acao(resposta)

        if not acao:
            return resposta

    contexto = obter_contexto()

    # -----------------------------
    # Ferramentas sem IP
    # -----------------------------

    if acao == "procurar":

        return executar_acao(acao)

    # -----------------------------
    # Demais ferramentas
    # -----------------------------

    ip = contexto.get("ip")

    if not ip:

        return """

Nenhuma impressora selecionada.

Use:

procurar impressoras

"""

    resultado = executar_acao(acao, ip)

    analise = analisar_resultados(resultado)

    atualizar({

        "ultima_acao": acao,

        "ultimo_resultado": resultado,

        "ultima_analise": analise

    })

    salvar({

        "ip": ip,

        "modelo": contexto.get("modelo"),

        "serial": contexto.get("serial"),

        "acao": acao,

        "resultado": resultado,

        "analise_tecnica": analise

    })

    arquivo = criar_relatorio({

        "ip": ip,

        "modelo": contexto.get("modelo"),

        "serial": contexto.get("serial"),

        "acao": acao,

        "resultado": resultado,

        "analise": analise

    })

    return f"""
=================================

AÇÃO EXECUTADA

=================================

Ferramenta:

{acao}

Resultado:

{resultado}

Análise Técnica:

{analise}

Relatório:

{arquivo}

=================================
"""