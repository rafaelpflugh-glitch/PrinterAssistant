import json
import os
from datetime import datetime


# ============================================================
# PRINTER ASSISTANT - GERADOR DE RELATÓRIO
# ============================================================

ARQUIVO_DADOS = "printer_data.json"
PASTA_RELATORIOS = "reports"


# ============================================================
# CONFIGURAÇÃO DE STATUS
# ============================================================

STATUS_ICONS = {

    "BOM": "[OK]",

    "ATENCAO": "[ATENCAO]",

    "BAIXO": "[BAIXO]",

    "CRITICO": "[CRITICO]",

    "DESCONHECIDO": "[?]"

}


# ============================================================
# CARREGAR DADOS
# ============================================================

def carregar_dados():

    if not os.path.exists(
        ARQUIVO_DADOS
    ):

        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_DADOS}"
        )


    with open(

        ARQUIVO_DADOS,

        "r",

        encoding="utf-8"

    ) as arquivo:

        return json.load(
            arquivo
        )


# ============================================================
# FORMATAR NÚMEROS
# ============================================================

def numero(valor):

    if valor is None:

        return "N/A"


    try:

        return f"{int(valor):,}".replace(
            ",",
            "."
        )

    except:

        return str(
            valor
        )


# ============================================================
# STATUS
# ============================================================

def status_supply(supply):

    status = supply.get(
        "status",
        "DESCONHECIDO"
    )


    return STATUS_ICONS.get(
        status,
        "[?]"
    )


# ============================================================
# NÍVEL VISUAL
# ============================================================

def barra_nivel(
    nivel,
    largura=30
):

    try:

        nivel = float(
            nivel
        )

    except:

        nivel = 0


    nivel = max(
        0,
        min(
            100,
            nivel
        )
    )


    preenchido = int(
        largura * nivel / 100
    )


    vazio = largura - preenchido


    return (

        "["
        + "#" * preenchido
        + "-" * vazio
        + "]"

    )


# ============================================================
# CLASSIFICAÇÃO GERAL
# ============================================================

def status_geral(supplies):

    if not supplies:

        return "SEM DADOS"


    niveis = []


    for supply in supplies:

        try:

            niveis.append(
                float(
                    supply.get(
                        "nivel",
                        0
                    )
                )
            )

        except:

            pass


    if not niveis:

        return "SEM DADOS"


    menor = min(
        niveis
    )


    if menor < 20:

        return "CRITICO"


    if menor < 40:

        return "BAIXO"


    if menor < 70:

        return "ATENCAO"


    return "BOM"


# ============================================================
# GERAR RELATÓRIO TEXTO
# ============================================================

def gerar_relatorio(dados):

    identificacao = dados.get(
        "identificacao",
        {}
    )


    snmp = dados.get(
        "snmp",
        {}
    )


    supplies = dados.get(
        "supplies",
        []
    )


    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )


    status = status_geral(
        supplies
    )


    linhas = []


    # ========================================================
    # CABEÇALHO
    # ========================================================

    linhas.append(
        "=" * 78
    )

    linhas.append(
        "PRINTER ASSISTANT - RELATORIO TECNICO"
    )

    linhas.append(
        "=" * 78
    )


    linhas.append("")


    linhas.append(
        f"Gerado em: {agora}"
    )


    linhas.append(
        f"IP: {dados.get('ip', 'N/A')}"
    )


    linhas.append("")


    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    linhas.append(
        "-" * 78
    )

    linhas.append(
        "IDENTIFICACAO DO EQUIPAMENTO"
    )

    linhas.append(
        "-" * 78
    )


    linhas.append("")


    linhas.append(
        f"Modelo       : "
        f"{identificacao.get('modelo', 'N/A')}"
    )


    linhas.append(
        f"Numero de serie: "
        f"{identificacao.get('serial', 'N/A')}"
    )


    linhas.append(
        f"Contador     : "
        f"{numero(identificacao.get('contador'))}"
    )


    linhas.append("")


    # ========================================================
    # CONECTIVIDADE
    # ========================================================

    linhas.append(
        "-" * 78
    )

    linhas.append(
        "CONECTIVIDADE"
    )

    linhas.append(
        "-" * 78
    )


    linhas.append("")


    linhas.append(
        "SNMP         : "
        + (
            "ATIVO"
            if snmp.get("ativo")
            else "INDISPONIVEL"
        )
    )


    linhas.append("")


    # ========================================================
    # STATUS GERAL
    # ========================================================

    linhas.append(
        "-" * 78
    )

    linhas.append(
        "STATUS GERAL"
    )

    linhas.append(
        "-" * 78
    )


    linhas.append("")


    linhas.append(
        f"Estado dos suprimentos: {status}"
    )


    linhas.append("")


    # ========================================================
    # SUPRIMENTOS
    # ========================================================

    linhas.append(
        "-" * 78
    )

    linhas.append(
        "SUPRIMENTOS"
    )

    linhas.append(
        "-" * 78
    )


    linhas.append("")


    if not supplies:

        linhas.append(
            "Nenhum suprimento monitorado."
        )

    else:

        for numero_supply, supply in enumerate(
            supplies,
            start=1
        ):

            nome = supply.get(
                "nome",
                "Desconhecido"
            )


            capacidade = supply.get(
                "capacidade"
            )


            restante = supply.get(
                "restante"
            )


            consumido = supply.get(
                "consumido"
            )


            nivel = supply.get(
                "nivel"
            )


            status_item = supply.get(
                "status",
                "DESCONHECIDO"
            )


            linhas.append(
                f"[{numero_supply}] {nome}"
            )


            linhas.append(
                f"    Status    : "
                f"{status_supply(supply)} "
                f"{status_item}"
            )


            linhas.append(
                f"    Nivel     : "
                f"{nivel}% "
                f"{barra_nivel(nivel)}"
            )


            linhas.append(
                f"    Capacidade: "
                f"{numero(capacidade)}"
            )


            linhas.append(
                f"    Restante  : "
                f"{numero(restante)}"
            )


            linhas.append(
                f"    Consumido : "
                f"{numero(consumido)}"
            )


            linhas.append("")


    # ========================================================
    # RODAPÉ
    # ========================================================

    linhas.append(
        "-" * 78
    )


    linhas.append(
        "Fim do relatorio."
    )


    linhas.append(
        "-" * 78
    )


    return "\n".join(
        linhas
    )


# ============================================================
# SALVAR RELATÓRIO
# ============================================================

def salvar_relatorio(
    texto,
    dados
):

    os.makedirs(
        PASTA_RELATORIOS,
        exist_ok=True
    )


    identificacao = dados.get(
        "identificacao",
        {}
    )


    modelo = identificacao.get(
        "modelo",
        "impressora"
    )


    serial = identificacao.get(
        "serial",
        "sem_serial"
    )


    modelo = str(
        modelo
    ).replace(
        " ",
        "_"
    )


    serial = str(
        serial
    ).replace(
        " ",
        "_"
    )


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


    nome_arquivo = (
        f"{modelo}_"
        f"{serial}_"
        f"{timestamp}.txt"
    )


    caminho = os.path.join(
        PASTA_RELATORIOS,
        nome_arquivo
    )


    with open(

        caminho,

        "w",

        encoding="utf-8"

    ) as arquivo:

        arquivo.write(
            texto
        )


    return caminho


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 78)
    print(
        "PRINTER ASSISTANT - GERADOR DE RELATORIO"
    )
    print("=" * 78)


    print()


    try:

        dados = carregar_dados()


    except Exception as erro:

        print(
            "ERRO:",
            erro
        )

        return


    texto = gerar_relatorio(
        dados
    )


    caminho = salvar_relatorio(
        texto,
        dados
    )


    print(
        texto
    )


    print()


    print("=" * 78)

    print(
        "RELATORIO GERADO COM SUCESSO"
    )

    print("=" * 78)


    print()

    print(
        "Arquivo:"
    )

    print(
        caminho
    )


    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()