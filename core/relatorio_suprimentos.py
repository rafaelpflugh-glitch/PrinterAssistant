"""
============================================================
PRINTER ASSISTANT
RELATÓRIO DE CONFIGURAÇÃO E SUPRIMENTOS
============================================================

Este módulo gera o relatório que acompanha a impressora
quando ela está pronta para ser embalada e enviada ao cliente.

O relatório funciona como uma "fotografia" do equipamento:

    - identificação da impressora;
    - configuração básica;
    - contador;
    - firmware;
    - endereço IP;
    - níveis dos suprimentos;
    - capacidade;
    - restante;
    - consumo;
    - número de série;
    - condição dos suprimentos.

IMPORTANTE
------------------------------------------------------------

Este módulo NÃO realiza nova coleta.

O PrinterDevice já deve estar previamente coletado.

Não chama:

    - device.coletar()
    - PJL
    - SYSDEBUG
    - SNMP
    - HTTP

Fluxo:

    PrinterDevice
          ↓
    extrair_dados()
          ↓
    montar_texto()
          ↓
    gerar_pcl()
          ↓
    imprimir()
          ↓
    Lexmark :9100

============================================================
"""

import socket
from datetime import datetime


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PORTA_RAW = 9100


# ============================================================
# ERRO
# ============================================================

class SuprimentosReportError(Exception):
    """
    Erro controlado do Relatório de Configuração e Suprimentos.
    """

    pass


# ============================================================
# UTILIDADES
# ============================================================

def texto(
    valor,
    padrao="N/D",
):
    """
    Converte um valor para texto legível.
    """

    if valor is None:
        return padrao

    valor = str(
        valor
    ).strip()

    if not valor:
        return padrao

    return valor


# ------------------------------------------------------------

def numero(
    valor,
    padrao="N/D",
):
    """
    Formata números usando ponto como separador
    de milhares.
    """

    if valor is None:
        return padrao

    try:

        return f"{int(valor):,}".replace(
            ",",
            ".",
        )

    except (
        TypeError,
        ValueError,
    ):

        return texto(
            valor,
            padrao,
        )


# ------------------------------------------------------------

def percentual(
    valor,
):
    """
    Formata percentual.

    O valor já deve vir normalizado pelo PrinterDevice.
    """

    if valor is None:
        return "N/D"

    try:

        return f"{float(valor):.1f} %"

    except (
        TypeError,
        ValueError,
    ):

        return texto(
            valor
        )


# ============================================================
# BARRA DE NÍVEL
# ============================================================

def barra_nivel(
    valor,
    largura=32,
):
    """
    Cria uma representação visual simples do nível
    do suprimento.
    """

    try:

        percentual_valor = float(
            valor
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            "["
            + ("-" * largura)
            + "]"
        )

    percentual_valor = max(
        0,
        min(
            100,
            percentual_valor,
        ),
    )

    preenchido = round(
        largura
        * percentual_valor
        / 100
    )

    vazio = (
        largura
        - preenchido
    )

    return (
        "["
        + ("#" * preenchido)
        + ("-" * vazio)
        + "]"
    )


# ============================================================
# TIPO DE SUPRIMENTO
# ============================================================

def tipo_supply(
    supply,
):
    """
    Determina o tipo do suprimento.

    O tipo é utilizado internamente para localizar
    os suprimentos.

    Ele não é repetido no relatório quando já está
    representado pelo título da seção.
    """

    if not isinstance(
        supply,
        dict,
    ):

        return ""

    tipo = supply.get(
        "tipo"
    )

    if tipo:

        tipo_normalizado = (
            str(
                tipo
            )
            .strip()
            .lower()
        )

        if tipo_normalizado in (
            "toner",
            "cartucho",
            "cartridge",
        ):

            return "toner"

        if tipo_normalizado in (
            "unidade_imagem",
            "unidade imagem",
            "imaging",
            "imaging unit",
            "photoconductor",
            "fotocondutor",
            "drum",
        ):

            return "unidade_imagem"

        if tipo_normalizado in (
            "fusor",
            "fuser",
            "maintenance",
            "maintenance kit",
            "kit manutenção",
            "kit manutenção",
        ):

            return "fusor"

    nome = (
        supply.get(
            "nome"
        )
        or
        supply.get(
            "name"
        )
        or
        supply.get(
            "descrição"
        )
        or
        supply.get(
            "description"
        )
        or
        ""
    )

    nome = str(
        nome
    ).strip().lower()

    if (
        "maintenance kit"
        in nome
    ):

        return "fusor"

    if (
        "fusor" in nome
        or
        "fuser" in nome
        or
        "maintenance" in nome
        or
        "manuten" in nome
    ):

        return "fusor"

    if (
        "toner" in nome
        or
        "cartucho" in nome
        or
        "cartridge" in nome
    ):

        return "toner"

    if (
        "unidade de imagem"
        in nome
        or
        "imaging unit"
        in nome
        or
        "imaging"
        in nome
        or
        "photoconductor"
        in nome
        or
        "drum"
        in nome
        or
        "fotocondutor"
        in nome
    ):

        return "unidade_imagem"

    return ""


# ============================================================
# LOCALIZAR SUPRIMENTO
# ============================================================

def encontrar_supply(
    supplies,
    tipo,
):
    """
    Localiza o primeiro suprimento do tipo solicitado.
    """

    if not isinstance(
        supplies,
        (list, tuple),
    ):

        return None

    for supply in supplies:

        if not isinstance(
            supply,
            dict,
        ):

            continue

        if tipo_supply(
            supply
        ) == tipo:

            return supply

    return None


# ============================================================
# STATUS
# ============================================================

def status_supply(
    supply,
):
    """
    Retorna a condição normalizada do suprimento.
    """

    if not isinstance(
        supply,
        dict,
    ):

        return "N/D"

    condição = supply.get(
        "condição"
    )

    if condição is None:

        return "N/D"

    condição = str(
        condição
    ).strip()

    if not condição:

        return "N/D"

    return condição


# ============================================================
# EXTRAIR DADOS DO DEVICE
# ============================================================

def extrair_dados(
    device,
):
    """
    Extrai os dados do PrinterDevice já coletado.

    NÃO realiza nova coleta.

    Retorna:

        identificação
        supplies
        ip
    """

    if device is None:

        raise SuprimentosReportError(
            "Nenhuma impressora foi fornecida."
        )

    # --------------------------------------------------------
    # Preferimos os atributos atuais do PrinterDevice.
    # --------------------------------------------------------

    identificação = getattr(
        device,
        "identificação",
        {},
    )

    supplies = getattr(
        device,
        "supplies",
        [],
    )

    ip = getattr(
        device,
        "ip",
        None,
    )

    # --------------------------------------------------------
    # Compatibilidade com objetos que possuem to_dict().
    # --------------------------------------------------------

    if (
        not isinstance(
            identificação,
            dict,
        )
        or
        not isinstance(
            supplies,
            list,
        )
        or
        not ip
    ):

        if hasattr(
            device,
            "to_dict",
        ):

            try:

                dados = device.to_dict()

            except Exception as erro:

                raise SuprimentosReportError(
                    "Não foi possível acessar os dados "
                    "do PrinterDevice."
                ) from erro

            if isinstance(
                dados,
                dict,
            ):

                if not isinstance(
                    identificação,
                    dict,
                ):

                    identificação = dados.get(
                        "identificação",
                        {},
                    )

                if not isinstance(
                    supplies,
                    list,
                ):

                    supplies = dados.get(
                        "supplies",
                        [],
                    )

                if not ip:

                    ip = dados.get(
                        "ip"
                    )

    if not isinstance(
        identificação,
        dict,
    ):

        identificação = {}

    if not isinstance(
        supplies,
        list,
    ):

        supplies = []

    return (
        identificação,
        supplies,
        ip,
    )


# ============================================================
# MONTAR RELATÓRIO
# ============================================================

def montar_texto(
    identificação,
    supplies,
    ip,
):
    """
    Monta o Relatório de Configuração e Suprimentos.

    Este relatório representa uma fotografia do equipamento
    no momento em que os dados foram coletados.

    NÃO realiza coleta.
    """

    fabricante = texto(
        identificação.get(
            "fabricante"
        ),
        "Lexmark",
    )

    modelo = texto(
        identificação.get(
            "modelo"
        )
    )

    família = texto(
        identificação.get(
            "família"
        )
    )

    tipo = texto(
        identificação.get(
            "tipo"
        )
    )

    serial = texto(
        identificação.get(
            "serial"
        )
    )

    contador = numero(
        identificação.get(
            "contador"
        )
    )

    firmware = texto(
        identificação.get(
            "firmware"
        )
    )

    toner = encontrar_supply(
        supplies,
        "toner",
    )

    unidade = encontrar_supply(
        supplies,
        "unidade_imagem",
    )

    fusor = encontrar_supply(
        supplies,
        "fusor",
    )

    agora = datetime.now()

    data_relatorio = agora.strftime(
        "%d/%m/%Y %H:%M"
    )

    # ========================================================
    # CABEÇALHO
    # ========================================================

    linhas = [

        "",

        "============================================================",

        "                    PRINTER ASSISTANT",

        "             RELATÓRIO TÉCNICO DE EQUIPAMENTO",

        "             CONFIGURAÇÃO E SUPRIMENTOS",

        "============================================================",

        "",

        f"  DATA DO RELATÓRIO : {data_relatorio}",

        f"  IP DO EQUIPAMENTO : {texto(ip)}",

        "",

        "------------------------------------------------------------",

        "                    IDENTIFICAÇÃO",

        "------------------------------------------------------------",

        f"  FABRICANTE        : {fabricante}",

        f"  MODELO            : {modelo}",

        f"  FAMÍLIA           : {família}",

        f"  TIPO              : {tipo}",

        f"  NÚMERO DE SÉRIE   : {serial}",

        f"  CONTADOR          : {contador}",

        f"  FIRMWARE          : {firmware}",

        "",

        "============================================================",

        "",

    ]

    # ========================================================
    # TONER
    # ========================================================

    linhas.extend(
        [

            "                         TONER",

            "------------------------------------------------------------",

        ]
    )

    if toner:

        linhas.extend(
            [

                f"  NÍVEL             : "
                f"{percentual(toner.get('nível'))}",

                f"  {barra_nivel(toner.get('nível'))}",

                "",

                f"  CAPACIDADE        : "
                f"{numero(toner.get('capacidade'))}",

                f"  RESTANTE          : "
                f"{numero(toner.get('restante'))}",

                f"  CONSUMIDO         : "
                f"{numero(toner.get('consumido'))}",

                f"  NÚMERO DE SÉRIE   : "
                f"{texto(toner.get('número_serie'))}",

                f"  CONDIÇÃO          : "
                f"{status_supply(toner)}",

            ]
        )

    else:

        linhas.extend(
            [

                "  NÍVEL             : N/D",

                "  [--------------------------------]",

                "",

                "  CAPACIDADE        : N/D",

                "  RESTANTE          : N/D",

                "  CONSUMIDO         : N/D",

                "  NÚMERO DE SÉRIE   : N/D",

                "  CONDIÇÃO          : N/D",

            ]
        )

    linhas.extend(
        [

            "",

            "------------------------------------------------------------",

            "",

            "",

        ]
    )

    # ========================================================
    # UNIDADE DE IMAGEM
    # ========================================================

    linhas.extend(
        [

            "                  UNIDADE DE IMAGEM",

            "------------------------------------------------------------",

        ]
    )

    if unidade:

        linhas.extend(
            [

                f"  NÍVEL             : "
                f"{percentual(unidade.get('nível'))}",

                f"  {barra_nivel(unidade.get('nível'))}",

                "",

                f"  CAPACIDADE        : "
                f"{numero(unidade.get('capacidade'))}",

                f"  RESTANTE          : "
                f"{numero(unidade.get('restante'))}",

                f"  CONSUMIDO         : "
                f"{numero(unidade.get('consumido'))}",

                f"  NÚMERO DE SÉRIE   : "
                f"{texto(unidade.get('número_serie'))}",

                f"  CONDIÇÃO          : "
                f"{status_supply(unidade)}",

            ]
        )

    else:

        linhas.extend(
            [

                "  NÍVEL             : N/D",

                "  [--------------------------------]",

                "",

                "  CAPACIDADE        : N/D",

                "  RESTANTE          : N/D",

                "  CONSUMIDO         : N/D",

                "  NÚMERO DE SÉRIE   : N/D",

                "  CONDIÇÃO          : N/D",

            ]
        )

    linhas.extend(
        [

            "",

            "------------------------------------------------------------",

            "",

            "",

        ]
    )

    # ========================================================
    # FUSOR / KIT DE MANUTENÇÃO
    # ========================================================

    linhas.extend(
        [

            "               FUSOR / KIT DE MANUTENÇÃO",

            "------------------------------------------------------------",

        ]
    )

    if fusor:

        linhas.extend(
            [

                f"  NÍVEL             : "
                f"{percentual(fusor.get('nível'))}",

                f"  {barra_nivel(fusor.get('nível'))}",

                "",

                f"  CAPACIDADE        : "
                f"{numero(fusor.get('capacidade'))}",

                f"  RESTANTE          : "
                f"{numero(fusor.get('restante'))}",

                f"  CONSUMIDO         : "
                f"{numero(fusor.get('consumido'))}",

                "  NÚMERO DE SÉRIE   : NÃO APLICÁVEL",

                f"  CONDIÇÃO          : "
                f"{status_supply(fusor)}",

            ]
        )

    else:

        linhas.extend(
            [

                "  NÍVEL             : N/D",

                "  [--------------------------------]",

                "",

                "  CAPACIDADE        : N/D",

                "  RESTANTE          : N/D",

                "  CONSUMIDO         : N/D",

                "  NÚMERO DE SÉRIE   : NÃO APLICÁVEL",

                "  CONDIÇÃO          : N/D",

            ]
        )

    linhas.extend(
        [

            "",

            "------------------------------------------------------------",

            "",

            "",

        ]
    )

    # ========================================================
    # RESUMO
    # ========================================================

    linhas.extend(
        [

            "                       RESUMO",

            "------------------------------------------------------------",

        ]
    )

    resumo = []

    if toner:

        resumo.append(
            f"  TONER             : "
            f"{percentual(toner.get('nível'))}"
            f"  |  {status_supply(toner)}"
        )

    if unidade:

        resumo.append(
            f"  UNIDADE DE IMAGEM : "
            f"{percentual(unidade.get('nível'))}"
            f"  |  {status_supply(unidade)}"
        )

    if fusor:

        resumo.append(
            f"  FUSOR             : "
            f"{percentual(fusor.get('nível'))}"
            f"  |  {status_supply(fusor)}"
        )

    if not resumo:

        resumo.append(
            "  Nenhum suprimento identificado."
        )

    linhas.extend(
        resumo
    )

    # ========================================================
    # RODAPÉ
    # ========================================================

    linhas.extend(
        [

            "",

            "------------------------------------------------------------",

            "",

            "  Relatório gerado pelo Printer Assistant.",

            "  Dados correspondentes ao equipamento no momento",

            "  da coleta realizada pelo sistema.",

            "",

            "============================================================",

            "                    FIM DO RELATÓRIO",

            "============================================================",

            "",

        ]
    )

    return "\r\n".join(
        linhas
    )


# ============================================================
# GERAR PCL
# ============================================================

def gerar_pcl(
    texto_relatorio,
):
    """
    Gera o job PCL enviado para a Lexmark.

    Utiliza A4 em retrato.

    ------------------------------------------------------------
    CODIFICAÇÃO
    ------------------------------------------------------------

    O texto interno do Python permanece em Unicode.

    Antes do envio à impressora, cada linha é convertida
    para CP850.

    O PCL é configurado para utilizar:

        12U = PC-850 Multilingual

    Essa combinação é adequada para os caracteres utilizados
    no português brasileiro:

        á é í ó ú
        Á É Í Ó Ú
        â ê ô
        Â Ê Ô
        ã õ
        Ã Õ
        ç Ç

    Fluxo:

        Python Unicode
              ↓
           CP850
              ↓
        PCL 12U
              ↓
           Lexmark

    NÃO utilizar UTF-8 neste job PCL.

    ------------------------------------------------------------
    FORMATAÇÃO
    ------------------------------------------------------------

    O espaçamento de 5 linhas por polegada deixa o relatório
    mais distribuído pela folha.
    """

    if not texto_relatorio:

        raise SuprimentosReportError(
            "O texto do relatório está vazio."
        )

    # ========================================================
    # INÍCIO DO JOB
    # ========================================================

    dados = b"\x1b%-12345X"

    # ========================================================
    # JOB PJL
    # ========================================================

    dados += (
        b'@PJL JOB NAME="PA_RELATORIO_SUPRIMENTOS"\r\n'
    )

    dados += (
        b"@PJL ENTER LANGUAGE=PCL\r\n"
    )

    # ========================================================
    # RESET
    # ========================================================

    dados += b"\x1bE"

    # ========================================================
    # PAPEL A4
    # ========================================================

    dados += b"\x1b&l26A"

    # ========================================================
    # RETRATO
    # ========================================================

    dados += b"\x1b&l0O"

    # ========================================================
    # MARGEM
    # ========================================================

    dados += b"\x1b&a5L"

    # ========================================================
    # ESPAÇAMENTO
    # ========================================================
    #
    # 5 linhas por polegada.
    #
    # O relatório fica mais espaçado e aproveita melhor
    # a área útil da folha.
    # ========================================================

    dados += b"\x1b&l5D"

    # ========================================================
    # FONTE
    # ========================================================
    #
    # CG Times, 10 pontos.
    # ========================================================

    fonte_corpo = (
        b"\x1b(s0p10h0s0b4099T"
    )

    dados += fonte_corpo

    # ========================================================
    # CONJUNTO DE SÍMBOLOS PCL
    # ========================================================
    #
    # 12U = PC-850 Multilingual
    #
    # A seleção é feita DEPOIS da fonte para garantir que
    # o conjunto de símbolos esteja ativo para o texto.
    #
    # Python Unicode
    #       ↓
    # CP850
    #       ↓
    # PCL 12U
    #       ↓
    # Lexmark
    #
    # ========================================================

    simbolos_pcl = b"\x1b(12U"

    dados += simbolos_pcl

    # ========================================================
    # NORMALIZAÇÃO DO TEXTO
    # ========================================================

    texto_limpo = (
        texto_relatorio
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
    )

    texto_limpo = texto_limpo.replace(
        "\t",
        "    ",
    )

    linhas = texto_limpo.split(
        "\n"
    )

    # ========================================================
    # TEXTO
    # ========================================================

    for linha in linhas:

        # ----------------------------------------------------
        # Reforça a fonte.
        # ----------------------------------------------------

        dados += fonte_corpo

        # ----------------------------------------------------
        # Reforça o conjunto de símbolos.
        # ----------------------------------------------------
        #
        # Mantemos 12U explicitamente associado ao texto.
        # Isso evita que uma seleção de fonte ou outro estado
        # PCL altere o conjunto de símbolos utilizado.
        # ----------------------------------------------------

        dados += simbolos_pcl

        # ----------------------------------------------------
        # CP850
        # ----------------------------------------------------
        #
        # A impressora está configurada para PCL 12U,
        # que corresponde ao conjunto PC-850.
        #
        # Não utilizar UTF-8 neste ponto.
        # Não utilizar Latin-1.
        # Não utilizar errors="replace".
        # ----------------------------------------------------

        try:

            linha_bytes = linha.encode(
                "cp850"
            )

        except UnicodeEncodeError as erro:

            raise SuprimentosReportError(
                "O relatório contém um caractere que não "
                "pode ser representado pelo conjunto "
                "PC-850 utilizado pelo PCL."
            ) from erro

        dados += linha_bytes

        dados += b"\r\n"

    # ========================================================
    # FORM FEED
    # ========================================================

    dados += b"\x0c"

    # ========================================================
    # FIM DO JOB
    # ========================================================

    dados += b"\x1b%-12345X"

    return dados


# ============================================================
# IMPRIMIR
# ============================================================

def imprimir(
    dados,
    ip,
    porta=PORTA_RAW,
):
    """
    Envia o PCL para a impressora.

    O IP é recebido do PrinterDevice.

    NÃO realiza descoberta.

    NÃO realiza coleta.
    """

    if not ip:

        raise SuprimentosReportError(
            "O endereço IP da impressora "
            "não está disponível."
        )

    if not dados:

        raise SuprimentosReportError(
            "O relatório PCL está vazio."
        )

    try:

        with socket.create_connection(
            (
                ip,
                porta,
            ),
            timeout=10,
        ) as sock:

            sock.sendall(
                dados
            )

    except OSError as erro:

        raise SuprimentosReportError(
            "Não foi possível enviar o relatório "
            f"para {ip}:{porta}.\n\n"
            f"{erro}"
        ) from erro

    return True


# ============================================================
# REPORT
# ============================================================

class ReportConfiguracaoSuprimentos:

    title = (
        "Configuração e Suprimentos"
    )

    description = (
        "Relatório técnico de configuração "
        "e suprimentos da impressora."
    )

    category = "Relatórios"

    def generate(
        self,
        session,
    ):
        """
        Gera e imprime o Relatório de Configuração
        e Suprimentos.

        'session' é o PrinterDevice já coletado.

        NÃO realiza nova coleta.
        """

        (
            identificação,
            supplies,
            ip,
        ) = extrair_dados(
            session
        )

        texto_relatorio = montar_texto(
            identificação,
            supplies,
            ip,
        )

        dados_pcl = gerar_pcl(
            texto_relatorio
        )

        imprimir(
            dados_pcl,
            ip,
            PORTA_RAW,
        )

        return {
            "sucesso": True,

            "relatório": (
                "configuração"
            ),

            "tipo": (
                "configuração_e_suprimentos"
            ),

            "ip": ip,

            "porta": PORTA_RAW,

            "bytes": len(
                dados_pcl
            ),

            "mensagem": (
                "Relatório de Configuração "
                "e Suprimentos enviado "
                "para a impressora."
            ),
        }


# ============================================================
# COMPATIBILIDADE
# ============================================================

ConfigReport = (
    ReportConfiguracaoSuprimentos
)


# ============================================================
# FUNÇÃO PÚBLICA
# ============================================================

def imprimir_relatorio_configuracao(
    device,
):
    """
    Função pública utilizada pelo ReportService.

    Recebe somente o PrinterDevice.

    NÃO recebe 'config' separado.

    NÃO realiza nova coleta.
    """

    if device is None:

        raise SuprimentosReportError(
            "Nenhuma impressora foi fornecida."
        )

    relatorio = (
        ReportConfiguracaoSuprimentos()
    )

    return relatorio.generate(
        device
    )


# ============================================================
# FIM DO RELATÓRIO
# ============================================================