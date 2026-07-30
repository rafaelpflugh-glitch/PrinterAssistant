import json
import os
from datetime import datetime


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DATA_FILE = "printer_data.json"

REPORTS_DIR = "reports"


# ============================================================
# UTILIDADES
# ============================================================

def carregar_dados():

    if not os.path.exists(DATA_FILE):

        raise FileNotFoundError(
            f"Arquivo não encontrado: {DATA_FILE}"
        )

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as arquivo:

        return json.load(arquivo)


def garantir_pasta():

    if not os.path.exists(REPORTS_DIR):

        os.makedirs(REPORTS_DIR)


def numero_formatado(valor):

    if valor is None:
        return "N/A"

    try:

        return f"{int(valor):,}".replace(",", ".")

    except:

        return str(valor)


# ============================================================
# ANÁLISE DOS SUPRIMENTOS
# ============================================================

def analisar_supply(supply):

    nome = supply.get(
        "nome",
        "Suprimento desconhecido"
    )

    nivel = supply.get(
        "nivel"
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

    status = supply.get(
        "status",
        ""
    ).upper()


    if nivel is None:

        return {

            "nome": nome,

            "nivel": None,

            "status": "DESCONHECIDO",

            "prioridade": "BAIXA",

            "mensagem":
                "Não foi possível determinar o nível."

        }


    # --------------------------------------------------------
    # Normalização
    # --------------------------------------------------------

    try:

        nivel = float(nivel)

    except:

        nivel = 0


    # --------------------------------------------------------
    # Classificação
    # --------------------------------------------------------

    if nivel >= 70:

        classificacao = "BOM"

        prioridade = "BAIXA"

        mensagem = (
            "Suprimento em nível normal. "
            "Nenhuma intervenção necessária."
        )


    elif nivel >= 40:

        classificacao = "ATENCAO"

        prioridade = "MEDIA"

        mensagem = (
            "Suprimento apresenta consumo significativo. "
            "Recomenda-se acompanhamento."
        )


    elif nivel >= 20:

        classificacao = "BAIXO"

        prioridade = "ALTA"

        mensagem = (
            "Suprimento em nível baixo. "
            "Recomenda-se planejar substituição."
        )


    else:

        classificacao = "CRITICO"

        prioridade = "CRITICA"

        mensagem = (
            "Suprimento em nível crítico. "
            "Substituição deve ser considerada em breve."
        )


    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    return {

        "nome": nome,

        "nivel": nivel,

        "capacidade": capacidade,

        "restante": restante,

        "consumido": consumido,

        "status_original": status,

        "status": classificacao,

        "prioridade": prioridade,

        "mensagem": mensagem

    }


# ============================================================
# ANÁLISE GERAL DOS SUPRIMENTOS
# ============================================================

def analisar_suprimentos(supplies):

    resultados = []

    criticos = 0

    baixos = 0

    atencao = 0

    bons = 0


    for supply in supplies:

        resultado = analisar_supply(
            supply
        )

        resultados.append(
            resultado
        )


        status = resultado["status"]


        if status == "CRITICO":

            criticos += 1


        elif status == "BAIXO":

            baixos += 1


        elif status == "ATENCAO":

            atencao += 1


        elif status == "BOM":

            bons += 1


    # --------------------------------------------------------
    # Estado geral
    # --------------------------------------------------------

    if criticos > 0:

        estado = "CRITICO"

        prioridade = "CRITICA"


    elif baixos > 0:

        estado = "BAIXO"

        prioridade = "ALTA"


    elif atencao > 0:

        estado = "ATENCAO"

        prioridade = "MEDIA"


    else:

        estado = "NORMAL"

        prioridade = "BAIXA"


    return {

        "estado_geral": estado,

        "prioridade": prioridade,

        "total": len(resultados),

        "bons": bons,

        "atencao": atencao,

        "baixos": baixos,

        "criticos": criticos,

        "itens": resultados

    }


# ============================================================
# ANÁLISE DO CONTADOR
# ============================================================

def analisar_contador(identificacao):

    contador = identificacao.get(
        "contador"
    )


    if contador is None:

        return {

            "contador": None,

            "status": "DESCONHECIDO",

            "mensagem":
                "Contador da impressora não disponível."

        }


    try:

        contador = int(contador)

    except:

        return {

            "contador": None,

            "status": "DESCONHECIDO",

            "mensagem":
                "Contador inválido."

        }


    # --------------------------------------------------------
    # Importante:
    #
    # O contador sozinho NÃO determina uma manutenção.
    #
    # Ele serve como contexto para diagnóstico.
    # --------------------------------------------------------

    if contador >= 200000:

        status = "ALTO"

        mensagem = (
            "Contador elevado. "
            "Recomenda-se verificar histórico de manutenção "
            "e componentes de desgaste."
        )


    elif contador >= 100000:

        status = "SIGNIFICATIVO"

        mensagem = (
            "Contador significativo. "
            "Componentes de desgaste devem ser acompanhados."
        )


    else:

        status = "NORMAL"

        mensagem = (
            "Contador dentro de uma faixa normal "
            "para acompanhamento geral."
        )


    return {

        "contador": contador,

        "status": status,

        "mensagem": mensagem

    }


# ============================================================
# ANÁLISE DE CONECTIVIDADE
# ============================================================

def analisar_conectividade(dados):

    snmp = dados.get(
        "snmp"
    )

    identificacao = dados.get(
        "identificacao",
        {}
    )


    # --------------------------------------------------------
    # O collector atual não salva explicitamente
    # um campo "snmp" booleano.
    #
    # Se houver supplies, consideramos SNMP funcional.
    # --------------------------------------------------------

    supplies = dados.get(
        "supplies",
        []
    )


    snmp_ativo = bool(
        supplies
    )


    pjl_ativo = bool(
        identificacao.get(
            "modelo"
        )
    )


    pontos = 0


    if snmp_ativo:

        pontos += 50


    if pjl_ativo:

        pontos += 50


    if pontos == 100:

        status = "EXCELENTE"


    elif pontos >= 50:

        status = "PARCIAL"


    else:

        status = "LIMITADA"


    return {

        "snmp": snmp_ativo,

        "pjl": pjl_ativo,

        "integracao": pontos,

        "status": status

    }


# ============================================================
# GERAÇÃO DE RECOMENDAÇÕES
# ============================================================

def gerar_recomendacoes(
    identificacao,
    suprimentos,
    conectividade
):

    recomendacoes = []


    # --------------------------------------------------------
    # Suprimentos
    # --------------------------------------------------------

    for item in suprimentos["itens"]:

        status = item["status"]

        nome = item["nome"]


        if status == "CRITICO":

            recomendacoes.append({

                "prioridade": "CRITICA",

                "tipo": "SUPRIMENTO",

                "item": nome,

                "acao":
                    f"Verificar imediatamente o suprimento '{nome}'."

            })


        elif status == "BAIXO":

            recomendacoes.append({

                "prioridade": "ALTA",

                "tipo": "SUPRIMENTO",

                "item": nome,

                "acao":
                    f"Planejar substituição de '{nome}'."

            })


        elif status == "ATENCAO":

            recomendacoes.append({

                "prioridade": "MEDIA",

                "tipo": "SUPRIMENTO",

                "item": nome,

                "acao":
                    f"Acompanhar consumo de '{nome}'."

            })


    # --------------------------------------------------------
    # Contador
    # --------------------------------------------------------

    contador = identificacao.get(
        "contador"
    )


    if contador is not None:

        try:

            contador = int(contador)


            if contador >= 200000:

                recomendacoes.append({

                    "prioridade": "ALTA",

                    "tipo": "MANUTENCAO",

                    "item": "Contador",

                    "acao":
                        "Verificar histórico de manutenção e "
                        "componentes de desgaste."

                })


            elif contador >= 100000:

                recomendacoes.append({

                    "prioridade": "MEDIA",

                    "tipo": "MANUTENCAO",

                    "item": "Contador",

                    "acao":
                        "Manter acompanhamento dos componentes "
                        "de desgaste."

                })


        except:

            pass


    # --------------------------------------------------------
    # Conectividade
    # --------------------------------------------------------

    if not conectividade["snmp"]:

        recomendacoes.append({

            "prioridade": "MEDIA",

            "tipo": "CONECTIVIDADE",

            "item": "SNMP",

            "acao":
                "SNMP não respondeu. Verificar configuração "
                "de gerenciamento da impressora."

        })


    if not conectividade["pjl"]:

        recomendacoes.append({

            "prioridade": "MEDIA",

            "tipo": "CONECTIVIDADE",

            "item": "PJL",

            "acao":
                "Identificação PJL não disponível."

        })


    # --------------------------------------------------------
    # Se não houver problemas
    # --------------------------------------------------------

    if not recomendacoes:

        recomendacoes.append({

            "prioridade": "BAIXA",

            "tipo": "GERAL",

            "item": "Equipamento",

            "acao":
                "Nenhuma intervenção imediata identificada."

        })


    return recomendacoes


# ============================================================
# DIAGNÓSTICO PRINCIPAL
# ============================================================

def diagnosticar(dados):

    identificacao = dados.get(
        "identificacao",
        {}
    )


    supplies = dados.get(
        "supplies",
        []
    )


    suprimentos = analisar_suprimentos(
        supplies
    )


    contador = analisar_contador(
        identificacao
    )


    conectividade = analisar_conectividade(
        dados
    )


    recomendacoes = gerar_recomendacoes(

        identificacao,

        suprimentos,

        conectividade

    )


    # --------------------------------------------------------
    # Estado geral do equipamento
    # --------------------------------------------------------

    if suprimentos["criticos"] > 0:

        estado = "CRITICO"


    elif suprimentos["baixos"] > 0:

        estado = "ATENCAO"


    elif suprimentos["atencao"] > 0:

        estado = "ACOMPANHAR"


    else:

        estado = "NORMAL"


    return {

        "data_diagnostico":
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "ip":
            dados.get(
                "ip"
            ),

        "identificacao":
            identificacao,

        "estado_geral":
            estado,

        "conectividade":
            conectividade,

        "contador":
            contador,

        "suprimentos":
            suprimentos,

        "recomendacoes":
            recomendacoes

    }


# ============================================================
# IMPRESSÃO DO DIAGNÓSTICO
# ============================================================

def imprimir_diagnostico(
    diagnostico
):

    identificacao = diagnostico[
        "identificacao"
    ]

    conectividade = diagnostico[
        "conectividade"
    ]

    contador = diagnostico[
        "contador"
    ]

    suprimentos = diagnostico[
        "suprimentos"
    ]

    recomendacoes = diagnostico[
        "recomendacoes"
    ]


    print()

    print("=" * 70)

    print(
        "PRINTER ASSISTANT - DIAGNOSTICO TECNICO"
    )

    print("=" * 70)


    print()

    print(
        "IP:",
        diagnostico["ip"]
    )

    print(
        "Modelo:",
        identificacao.get(
            "modelo",
            "Desconhecido"
        )
    )

    print(
        "Serial:",
        identificacao.get(
            "serial",
            "Desconhecido"
        )
    )


    print()

    print("-" * 70)

    print(
        "ESTADO GERAL"
    )

    print("-" * 70)


    print(
        "Estado:",
        diagnostico["estado_geral"]
    )

    print(
        "Prioridade:",
        suprimentos["prioridade"]
    )


    print()

    print("-" * 70)

    print(
        "CONECTIVIDADE"
    )

    print("-" * 70)


    print(
        "SNMP:",
        "ATIVO"
        if conectividade["snmp"]
        else "INATIVO"
    )


    print(
        "PJL:",
        "ATIVO"
        if conectividade["pjl"]
        else "INATIVO"
    )


    print(
        "Integração:",
        f'{conectividade["integracao"]}%'
    )


    print(
        "Status:",
        conectividade["status"]
    )


    print()

    print("-" * 70)

    print(
        "CONTADOR"
    )

    print("-" * 70)


    if contador["contador"] is not None:

        print(
            "Páginas:",
            numero_formatado(
                contador["contador"]
            )
        )


    print(
        "Status:",
        contador["status"]
    )


    print(
        contador["mensagem"]
    )


    print()

    print("-" * 70)

    print(
        "SUPRIMENTOS"
    )

    print("-" * 70)


    for i, item in enumerate(

        suprimentos["itens"],

        start=1

    ):

        print()

        print(
            f"[{i}] {item['nome']}"
        )


        print(
            "    Nível:",
            f"{item['nivel']:.1f}%"
            if item["nivel"] is not None
            else "N/A"
        )


        print(
            "    Capacidade:",
            numero_formatado(
                item.get(
                    "capacidade"
                )
            )
        )


        print(
            "    Restante:",
            numero_formatado(
                item.get(
                    "restante"
                )
            )
        )


        print(
            "    Consumido:",
            numero_formatado(
                item.get(
                    "consumido"
                )
            )
        )


        print(
            "    Status:",
            item["status"]
        )


        print(
            "    Análise:",
            item["mensagem"]
        )


    print()

    print("-" * 70)

    print(
        "RECOMENDAÇÕES"
    )

    print("-" * 70)


    for i, item in enumerate(

        recomendacoes,

        start=1

    ):

        print()

        print(
            f"[{i}] "
            f"[{item['prioridade']}] "
            f"{item['tipo']}"
        )


        print(
            "    Item:",
            item["item"]
        )


        print(
            "    Ação:",
            item["acao"]
        )


    print()

    print("=" * 70)

    print(
        "FIM DO DIAGNOSTICO"
    )

    print("=" * 70)


# ============================================================
# SALVAR DIAGNÓSTICO
# ============================================================

def salvar_diagnostico(
    diagnostico
):

    garantir_pasta()


    modelo = diagnostico[
        "identificacao"
    ].get(
        "modelo",
        "impressora"
    )


    serial = diagnostico[
        "identificacao"
    ].get(
        "serial",
        "sem_serial"
    )


    nome_modelo = (

        str(modelo)

        .replace(
            " ",
            "_"
        )

        .replace(
            "/",
            "-"
        )

    )


    nome_serial = (

        str(serial)

        .replace(
            " ",
            "_"
        )

        .replace(
            "/",
            "-"
        )

    )


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


    arquivo = os.path.join(

        REPORTS_DIR,

        (
            f"diagnostico_"
            f"{nome_modelo}_"
            f"{nome_serial}_"
            f"{timestamp}.json"
        )

    )


    with open(

        arquivo,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            diagnostico,

            f,

            indent=4,

            ensure_ascii=False

        )


    return arquivo


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "PRINTER ASSISTANT - MOTOR DE DIAGNOSTICO"
    )

    print("=" * 70)


    print()

    print(
        "Carregando:",
        DATA_FILE
    )


    try:

        dados = carregar_dados()


    except Exception as erro:

        print()

        print(
            "ERRO:",
            erro
        )

        return


    diagnostico = diagnosticar(
        dados
    )


    imprimir_diagnostico(
        diagnostico
    )


    arquivo = salvar_diagnostico(
        diagnostico
    )


    print()

    print(
        "Diagnóstico salvo em:"
    )

    print(
        arquivo
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()