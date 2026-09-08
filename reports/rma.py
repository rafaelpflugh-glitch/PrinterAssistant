"""
============================================================
PRINTER ASSISTANT
RELATÓRIO RMA
============================================================

Etiqueta de RMA para unidade de imagem.

A etiqueta contém SOMENTE:

    - SERIAL da unidade de imagem testada;
    - código de barras CODE 128 do SERIAL;
    - FABRICANTE;
    - STARTER: SIM ou NAO;
    - DEFEITO: FALHAS;
    - NIVEL em percentual;
    - LOTE em branco para preenchimento manual.

IMPRESSORA DA ETIQUETA:

    TSC
    IP: 192.168.14.151
    RAW: 9100

FORMATO DA ETIQUETA:

    100 x 150 mm
    GAP: 2 mm

IMPORTANTE:

    O IP definido neste módulo identifica SOMENTE a TSC.

    A impressora/dispositivo que forneceu os dados da
    unidade de imagem NÃO é usada como destino de impressão.

    Este módulo NÃO depende de modelo específico de
    impressora.

    Este módulo NÃO depende de MX611.

    O device recebido é utilizado apenas para acessar os
    dados já coletados da UST.

    NÃO realiza nova coleta de rede.

------------------------------------------------------------
SYSDEBUG / STARTER
------------------------------------------------------------

    O Starter é determinado a partir dos dados já coletados
    e do SYSDEBUG que já foi coletado e salvo pelo Printer
    Assistant.

    O RMA NÃO consulta a impressora novamente.

    O RMA NÃO altera o parser SYSDEBUG.

    O RMA NÃO depende de raw_sysdebug no objeto device.

    O RMA localiza o SYSDEBUG salvo procurando o SERIAL da
    unidade de imagem.

    REGRA:

        MS622 / MS622de
            -> NÃO STARTER

        Demais modelos:

            AM IU
                -> NÃO STARTER

            AM IU ausente
                -> STARTER

    Para a detecção tradicional, a linha deve ser exatamente:

        AM IU

    Depois de normalizados espaços e caracteres invisíveis.

    NÃO são utilizados na regra tradicional:

        - part number;
        - SKU;
        - ST;
        - SWE;
        - descrição;
        - qualquer outra nomenclatura.

    Se o SYSDEBUG correspondente não puder ser encontrado
    nos arquivos já salvos, o RMA gera RMAError.

------------------------------------------------------------
DESEMPENHO
------------------------------------------------------------

    A procura do SYSDEBUG é feita diretamente nos bytes do
    arquivo.

    O HTML NÃO é limpo/processado durante a procura.

    O HTML só é convertido para texto depois que o arquivo
    correto foi encontrado.

    Isso evita processar arquivos de SYSDEBUG de vários MB
    desnecessariamente.

    Além disso, o resultado do Starter é mantido em cache
    durante a execução, evitando repetir a procura quando
    o operador clica em IMPRIMIR.

============================================================
"""

from __future__ import annotations

import html
import re
import socket
import time
from pathlib import Path


# ============================================================
# TIMER
# ============================================================

def _rma_log(t0, etapa):
    print(
        f"[RMA-TIMER] {time.perf_counter() - t0:8.3f}s | {etapa}",
        flush=True,
    )


# ============================================================
# CONFIGURAÇÃO DA TSC
# ============================================================

TSC_IP = "192.168.14.151"
TSC_PORTA = 9100


# ============================================================
# CONFIGURAÇÃO FÍSICA DA ETIQUETA
# ============================================================

ETIQUETA_LARGURA_MM = 100
ETIQUETA_ALTURA_MM = 150
GAP_MM = 2


# ============================================================
# CONFIGURAÇÃO DOS SYSDEBUGS SALVOS
# ============================================================

LOG_DIR = (
    Path(__file__).resolve().parent.parent
    / "logs"
    / "sysdebug"
)


# ============================================================
# FABRICANTES ACEITOS
# ============================================================

FABRICANTE_LEXMARK = "LEXMARK"
FABRICANTE_GLOBAL = "GLOBAL"

FABRICANTES_VALIDOS = (
    FABRICANTE_LEXMARK,
    FABRICANTE_GLOBAL,
)


# ============================================================
# VALORES FIXOS DA ETIQUETA
# ============================================================

DEFEITO_RMA = "FALHAS"


# ============================================================
# CACHE DO SYSDEBUG / STARTER
# ============================================================

# Evita que a segunda chamada de preparar_rma(), feita
# quando o operador clica em IMPRIMIR, procure novamente
# o mesmo SYSDEBUG.
#
# Chave:
#
#     serial
#
# Valor:
#
#     True  -> Starter
#     False -> Não Starter

_STARTER_CACHE = {}


# ============================================================
# ERRO
# ============================================================

class RMAError(Exception):
    """
    Erro controlado durante preparação ou impressão
    da etiqueta RMA.
    """

    pass


# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def _texto(valor, padrao=""):
    """
    Converte um valor para texto limpo.
    """

    if valor is None:
        return padrao

    return str(valor).strip()


# ============================================================
# LIMPAR TEXTO PARA TSPL
# ============================================================

def _texto_tspl(valor):
    """
    Prepara texto para utilização dentro de uma string
    TSPL delimitada por aspas.
    """

    texto = _texto(valor)

    texto = texto.replace('"', "'")
    texto = texto.replace("\r", " ")
    texto = texto.replace("\n", " ")

    return texto


# ============================================================
# LIMPAR HTML DO SYSDEBUG
# ============================================================

def _limpar_html_sysdebug(texto):
    """
    Converte o HTML salvo pelo módulo SYSDEBUG em texto.

    IMPORTANTE:

        Esta função NÃO é utilizada para procurar o arquivo.

        Ela só é chamada depois que o arquivo correto foi
        localizado pelo serial.

    Isso evita processar vários arquivos grandes de SYSDEBUG.
    """

    if not texto:
        return ""

    texto = html.unescape(str(texto))

    texto = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    texto = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    texto = re.sub(
        r"<br\s*/?>",
        "\n",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"</(?:p|div|tr|li|h[1-6])\s*>",
        "\n",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"<[^>]+>",
        " ",
        texto,
    )

    texto = (
        texto
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    texto = re.sub(
        r"[ \t]+",
        " ",
        texto,
    )

    texto = re.sub(
        r"\n\s*\n+",
        "\n",
        texto,
    )

    return texto.strip()


# ============================================================
# NORMALIZAR LINHA DO SYSDEBUG
# ============================================================

def _normalizar_linha_sysdebug(linha):
    """
    Normaliza uma linha para comparação.

    Exemplos:

        AM IU        -> AM IU
         AM IU      -> AM IU
        AM   IU     -> AM IU
        AM IU<NBSP> -> AM IU

    NÃO transforma:

        ST AM IU
        AM IU XYZ
    """

    if not isinstance(linha, str):
        return ""

    texto = (
        linha
        .replace("\ufeff", "")
        .replace("\xa0", " ")
    )

    texto = " ".join(texto.split())

    return texto.upper().strip()


# ============================================================
# LINHA AM IU
# ============================================================

def _linha_eh_am_iu(linha):
    """
    Retorna True SOMENTE quando a linha inteira corresponde
    a AM IU.
    """

    return (
        _normalizar_linha_sysdebug(linha)
        == "AM IU"
    )


# ============================================================
# LOCALIZAR UNIDADE DE IMAGEM
# ============================================================

def _obter_unidade_imagem(device):
    """
    Localiza a unidade de imagem nos dados já coletados.

    NÃO realiza comunicação de rede.

    Apenas chama device.to_dict().
    """

    if device is None:
        raise RMAError(
            "Nenhuma UST está selecionada."
        )

    try:
        dados = device.to_dict()
    except Exception as erro:
        raise RMAError(
            "Não foi possível obter os dados "
            "da UST.\n\n"
            f"{erro}"
        ) from erro

    if not isinstance(dados, dict):
        raise RMAError(
            "Os dados da UST não possuem "
            "o formato esperado."
        )

    supplies = dados.get(
        "supplies",
        [],
    )

    if not isinstance(
        supplies,
        list,
    ):
        supplies = []

    # --------------------------------------------------------
    # TERMOS QUE IDENTIFICAM UNIDADE DE IMAGEM
    # --------------------------------------------------------

    termos_tipo = (
        "unidade_imagem",
        "unidade imagem",
        "imaging unit",
        "imaging",
        "photoconductor",
        "fotocondutor",
        "drum",
    )

    termos_nome = (
        "unidade de imagem",
        "unidade imagem",
        "imaging unit",
        "imaging",
        "photoconductor",
        "fotocondutor",
        "drum",
    )

    # --------------------------------------------------------
    # PROCURA
    # --------------------------------------------------------

    for supply in supplies:

        if not isinstance(
            supply,
            dict,
        ):
            continue

        tipo = _texto(
            supply.get("tipo")
        ).lower()

        nome = _texto(
            supply.get("nome")
            or supply.get("name")
            or supply.get("descricao")
            or supply.get("description")
        ).lower()

        if any(
            termo in tipo
            for termo in termos_tipo
        ):
            return supply

        if any(
            termo in nome
            for termo in termos_nome
        ):
            return supply

    raise RMAError(
        "Não foi encontrada uma unidade "
        "de imagem nos dados coletados da UST."
    )


# ============================================================
# SERIAL DA UNIDADE DE IMAGEM
# ============================================================

def _obter_serial_unidade_imagem(unidade):
    """
    Obtém o número de série da unidade de imagem.
    """

    if not isinstance(
        unidade,
        dict,
    ):
        raise RMAError(
            "Dados inválidos da unidade de imagem."
        )

    serial = (
        unidade.get("numero_serie")
        or unidade.get("serial")
    )

    serial = _texto(serial)

    if not serial:
        raise RMAError(
            "A unidade de imagem encontrada "
            "não possui número de série."
        )

    return serial


# ============================================================
# NÍVEL DA UNIDADE DE IMAGEM
# ============================================================

def _obter_nivel_unidade_imagem(unidade):
    """
    Obtém o nível percentual da unidade de imagem.

    O valor é limitado entre 0 e 100.
    """

    nivel = unidade.get(
        "nivel"
    )

    if nivel is None:
        nivel = unidade.get(
            "percentual"
        )

    try:
        nivel = float(nivel)
    except (
        TypeError,
        ValueError,
    ):
        nivel = 0

    nivel = max(
        0,
        min(
            100,
            nivel,
        ),
    )

    return nivel


# ============================================================
# OBTENER MODELO DOS DADOS JÁ COLETADOS
# ============================================================

def _obter_modelo_device(device):
    """
    Obtém o modelo a partir dos dados já coletados do device.

    NÃO realiza nova coleta de rede.

    Este dado é utilizado SOMENTE para a exceção conhecida
    do MS622/MS622de na classificação Starter.

    Se o modelo não puder ser obtido, retorna "".
    """

    if device is None:
        return ""

    try:
        dados = device.to_dict()
    except Exception:
        return ""

    if not isinstance(dados, dict):
        return ""

    identificacao = dados.get(
        "identificacao",
        {},
    )

    if not isinstance(
        identificacao,
        dict,
    ):
        identificacao = {}

    modelo = (
        identificacao.get("modelo")
        or dados.get("modelo")
        or getattr(
            device,
            "modelo",
            None,
        )
    )

    return _texto(modelo)


# ============================================================
# MS622 / MS622de
# ============================================================

def _modelo_e_ms622(modelo):
    """
    Retorna True quando o modelo corresponde à família MS622.

    Exemplos aceitos:

        MS622
        MS622de
        Lexmark MS622de

    A comparação é feita apenas sobre o modelo já coletado.
    """

    modelo = _texto(modelo).upper()

    if not modelo:
        return False

    modelo_normalizado = re.sub(
        r"[^A-Z0-9]",
        "",
        modelo,
    )

    return modelo_normalizado.startswith(
        "LEXMARKMS622"
    ) or modelo_normalizado.startswith(
        "MS622"
    )


# ============================================================
# LOCALIZAR SYSDEBUG SALVO PELO SERIAL
# ============================================================

def _localizar_sysdebug_salvo(serial):
    """
    Procura o SYSDEBUG já salvo que contém o serial da
    unidade de imagem.

    OTIMIZAÇÃO IMPORTANTE:

        A versão anterior fazia:

            arquivo -> ler texto -> limpar HTML -> regex
            para cada arquivo

        Isso era extremamente caro porque os SYSDEBUGs podem
        possuir vários MB.

        Agora fazemos:

            arquivo -> ler bytes -> procurar serial

        A limpeza do HTML só acontece depois que o arquivo
        correto foi encontrado.

    O arquivo mais recente é testado primeiro.

    Retorna:

        (caminho_do_arquivo, texto_limpo)
    """

    t0 = time.perf_counter()

    serial = _texto(serial)

    if not serial:
        raise RMAError(
            "Serial inválido para localizar "
            "o SYSDEBUG salvo."
        )

    serial_bytes = serial.upper().encode(
        "ascii",
        errors="ignore",
    )

    if not serial_bytes:
        raise RMAError(
            "Não foi possível preparar o serial "
            "para localizar o SYSDEBUG."
        )

    if not LOG_DIR.exists():
        raise RMAError(
            "A pasta de SYSDEBUGs salvos não foi encontrada.\n\n"
            f"Pasta esperada:\n{LOG_DIR}"
        )

    # --------------------------------------------------------
    # LOCALIZAR ARQUIVOS
    # --------------------------------------------------------

    try:
        arquivos = list(
            LOG_DIR.rglob("*.html")
        )
    except Exception as erro:
        raise RMAError(
            "Não foi possível procurar os SYSDEBUGs salvos.\n\n"
            f"Pasta:\n{LOG_DIR}\n\n"
            f"{erro}"
        ) from erro

    if not arquivos:
        raise RMAError(
            "Nenhum SYSDEBUG salvo foi encontrado.\n\n"
            f"Pasta:\n{LOG_DIR}"
        )

    # --------------------------------------------------------
    # MAIS RECENTE PRIMEIRO
    # --------------------------------------------------------

    try:
        arquivos.sort(
            key=lambda arquivo: arquivo.stat().st_mtime,
            reverse=True,
        )
    except Exception:
        pass

    _rma_log(
        t0,
        f"SYSDEBUG: {len(arquivos)} arquivo(s) candidato(s)"
    )

    # --------------------------------------------------------
    # PROCURAR SERIAL DIRETAMENTE NOS BYTES
    # --------------------------------------------------------

    for indice, arquivo in enumerate(
        arquivos,
        start=1,
    ):

        try:
            conteudo_bytes = arquivo.read_bytes()
        except Exception:
            continue

        if not conteudo_bytes:
            continue

        # ----------------------------------------------------
        # Busca extremamente mais barata do que limpar HTML.
        # ----------------------------------------------------

        if serial_bytes not in conteudo_bytes.upper():
            continue

        # ----------------------------------------------------
        # ENCONTRADO
        # ----------------------------------------------------

        _rma_log(
            t0,
            f"SYSDEBUG encontrado: {arquivo.name}"
        )

        _rma_log(
            t0,
            f"Posição na busca: {indice}/{len(arquivos)}"
        )

        # ----------------------------------------------------
        # AGORA SIM limpar HTML.
        #
        # Só fazemos isso no arquivo correto.
        # ----------------------------------------------------

        try:
            conteudo = conteudo_bytes.decode(
                "utf-8",
                errors="ignore",
            )
        except Exception as erro:
            raise RMAError(
                "O SYSDEBUG correspondente foi encontrado, "
                "mas não pôde ser convertido para texto.\n\n"
                f"Arquivo:\n{arquivo}\n\n"
                f"{erro}"
            ) from erro

        texto_limpo = _limpar_html_sysdebug(
            conteudo
        )

        _rma_log(
            t0,
            "SYSDEBUG encontrado e HTML processado"
        )

        return (
            arquivo,
            texto_limpo,
        )

    # --------------------------------------------------------
    # NÃO ENCONTRADO
    # --------------------------------------------------------

    raise RMAError(
        "Não foi encontrado um SYSDEBUG salvo "
        "correspondente à unidade de imagem.\n\n"
        f"Serial procurado:\n{serial}\n\n"
        f"Pasta pesquisada:\n{LOG_DIR}\n\n"
        "O RMA não irá assumir STARTER."
    )


# ============================================================
# EXTRAIR BLOCO DA UNIDADE PELO SERIAL
# ============================================================

def _obter_bloco_unidade_por_serial(
    texto,
    serial,
):
    """
    Localiza no SYSDEBUG o bloco correspondente ao serial
    da unidade de imagem.

    O bloco começa preferencialmente em:

        Mono Cartridge Imaging Unit

    e termina antes de outro:

        S/N:

    ou no fim do SYSDEBUG.
    """

    if not isinstance(
        texto,
        str,
    ):
        return None

    serial = _texto(
        serial
    ).upper()

    if not serial:
        return None

    texto = (
        texto
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    linhas = texto.split("\n")

    indice_serial = None

    # --------------------------------------------------------
    # PROCURAR SERIAL
    # --------------------------------------------------------

    for indice, linha in enumerate(
        linhas
    ):
        if serial in linha.upper():
            indice_serial = indice
            break

    if indice_serial is None:
        return None

    # --------------------------------------------------------
    # DETERMINAR INÍCIO DO BLOCO
    # --------------------------------------------------------

    inicio = indice_serial

    limite_inicio = max(
        0,
        indice_serial - 20,
    )

    for indice in range(
        indice_serial - 1,
        limite_inicio - 1,
        -1,
    ):

        linha = _normalizar_linha_sysdebug(
            linhas[indice]
        )

        if (
            "MONO CARTRIDGE IMAGING UNIT"
            in linha
        ):
            inicio = indice
            break

    # --------------------------------------------------------
    # DETERMINAR FIM DO BLOCO
    # --------------------------------------------------------

    fim = len(linhas)

    for indice in range(
        indice_serial + 1,
        len(linhas),
    ):

        linha = _normalizar_linha_sysdebug(
            linhas[indice]
        )

        if linha.startswith(
            "S/N:"
        ):

            if serial not in linha:
                fim = indice
                break

    bloco = "\n".join(
        linhas[inicio:fim]
    )

    return bloco


# ============================================================
# DETECTAR STARTER PELO SYSDEBUG SALVO
# ============================================================

def _detectar_starter_no_sysdebug_salvo(
    serial,
    modelo="",
):
    """
    Determina o Starter usando os dados já coletados e o
    SYSDEBUG já salvo.

    REGRA ESPECIAL:

        MS622 / MS622de
            -> NÃO STARTER

    Para os demais modelos:

        AM IU encontrado no bloco
            -> NÃO STARTER

        AM IU não encontrado no bloco
            -> STARTER

    Não utiliza:

        - nova coleta de rede
        - raw_sysdebug
        - parser
        - part number
        - SKU
        - ST
        - SWE
        - nome
        - descrição

    O resultado é armazenado em cache por serial.
    """

    t0 = time.perf_counter()

    serial = _texto(
        serial
    )

    if not serial:
        raise RMAError(
            "Não é possível detectar Starter "
            "sem o serial da unidade de imagem."
        )

    # ========================================================
    # CACHE
    # ========================================================

    chave_cache = serial.upper()

    if chave_cache in _STARTER_CACHE:

        resultado = _STARTER_CACHE[
            chave_cache
        ]

        _rma_log(
            t0,
            f"STARTER obtido do CACHE: "
            f"{'SIM' if resultado else 'NAO'}"
        )

        return resultado

    # ========================================================
    # REGRA ESPECÍFICA MS622
    # ========================================================

    if _modelo_e_ms622(modelo):

        resultado = False

        _STARTER_CACHE[
            chave_cache
        ] = resultado

        _rma_log(
            t0,
            f"MODELO {modelo} -> MS622 NÃO STARTER"
        )

        return resultado

    # ========================================================
    # LOCALIZAR SYSDEBUG
    # ========================================================

    _rma_log(
        t0,
        "ANTES DE localizar SYSDEBUG salvo"
    )

    arquivo, texto = (
        _localizar_sysdebug_salvo(
            serial
        )
    )

    _rma_log(
        t0,
        "DEPOIS DE localizar SYSDEBUG salvo"
    )

    bloco = _obter_bloco_unidade_por_serial(
        texto,
        serial,
    )

    if not bloco:
        raise RMAError(
            "O SYSDEBUG salvo foi encontrado, "
            "mas não foi possível localizar o bloco "
            "correspondente à unidade de imagem.\n\n"
            f"Serial:\n{serial}\n\n"
            f"Arquivo:\n{arquivo}"
        )

    _rma_log(
        t0,
        "BLOCO DA UNIDADE LOCALIZADO"
    )

    # ========================================================
    # REGRA TRADICIONAL
    # ========================================================

    linhas = bloco.split(
        "\n"
    )

    for linha in linhas:

        if _linha_eh_am_iu(
            linha
        ):

            # AM IU = NÃO STARTER

            resultado = False

            _STARTER_CACHE[
                chave_cache
            ] = resultado

            _rma_log(
                t0,
                "AM IU encontrado -> NÃO STARTER"
            )

            return resultado

    # ========================================================
    # AM IU AUSENTE = STARTER
    # ========================================================

    resultado = True

    _STARTER_CACHE[
        chave_cache
    ] = resultado

    _rma_log(
        t0,
        "AM IU ausente -> STARTER"
    )

    return resultado


# ============================================================
# TEXTO DO STARTER
# ============================================================

def _texto_starter(starter):
    """
    Converte o resultado da detecção para SIM ou NAO.
    """

    return (
        "SIM"
        if bool(starter)
        else "NAO"
    )


# ============================================================
# VALIDAR FABRICANTE
# ============================================================

def _validar_fabricante(fabricante):
    """
    Valida o fabricante informado pelo operador.

    Fabricantes permitidos:

        LEXMARK
        GLOBAL
    """

    fabricante = _texto(
        fabricante,
        FABRICANTE_LEXMARK,
    ).upper()

    if fabricante not in FABRICANTES_VALIDOS:
        raise RMAError(
            "Fabricante inválido.\n\n"
            "Escolha LEXMARK ou GLOBAL."
        )

    return fabricante


# ============================================================
# PREPARAR DADOS DA RMA
# ============================================================

def preparar_rma(
    device,
    fabricante=FABRICANTE_LEXMARK,
    lote="",
):
    """
    Prepara os dados da etiqueta RMA.

    NÃO imprime.
    NÃO realiza coleta.
    NÃO comunica com a TSC.
    NÃO consulta a impressora da UST.

    O Starter é determinado pelo SYSDEBUG já salvo,
    com a exceção conhecida do MS622/MS622de.
    """

    _t0 = time.perf_counter()

    _rma_log(
        _t0,
        "ENTROU EM preparar_rma"
    )

    _rma_log(
        _t0,
        "ANTES DE _obter_unidade_imagem / device.to_dict()"
    )

    unidade = _obter_unidade_imagem(
        device
    )

    _rma_log(
        _t0,
        "DEPOIS DE _obter_unidade_imagem / device.to_dict()"
    )

    serial = _obter_serial_unidade_imagem(
        unidade
    )

    _rma_log(
        _t0,
        "DEPOIS DE obter serial"
    )

    nivel = _obter_nivel_unidade_imagem(
        unidade
    )

    _rma_log(
        _t0,
        "DEPOIS DE obter nivel"
    )

    fabricante = _validar_fabricante(
        fabricante
    )

    # --------------------------------------------------------
    # MODELO
    #
    # Obtido somente dos dados já coletados do device.
    # NÃO realiza nova comunicação.
    #
    # É usado exclusivamente para reconhecer a exceção
    # conhecida do MS622/MS622de.
    # --------------------------------------------------------

    modelo = _obter_modelo_device(
        device
    )

    _rma_log(
        _t0,
        f"MODELO PARA REGRA STARTER: {modelo or 'DESCONHECIDO'}"
    )

    # --------------------------------------------------------
    # STARTER
    # --------------------------------------------------------

    started = _detectar_starter_no_sysdebug_salvo(
        serial,
        modelo=modelo,
    )

    _rma_log(
        _t0,
        "DEPOIS DE detectar_starter_no_sysdebug_salvo"
    )

    lote = _texto(
        lote
    )

    _rma_log(
        _t0,
        "SAINDO DE preparar_rma"
    )

    return {
        "serial": serial,
        "nivel": nivel,
        "fabricante": fabricante,
        "started": started,
        "starter": started,
        "starter_texto": _texto_starter(
            started
        ),
        "defeito": DEFEITO_RMA,
        "lote": lote,
    }


# ============================================================
# GERAR TSPL
# ============================================================

def gerar_etiqueta_rma(
    serial,
    fabricante=FABRICANTE_LEXMARK,
    started=False,
    nivel=0,
    lote="",
):
    """
    Gera o comando TSPL completo da etiqueta RMA.

    Formato físico:

        100 x 150 mm
        GAP 2 mm

    Layout vertical utilizando melhor a área física
    da etiqueta.
    """

    _t0 = time.perf_counter()

    _rma_log(
        _t0,
        "ENTROU EM gerar_etiqueta_rma"
    )

    # --------------------------------------------------------
    # SERIAL
    # --------------------------------------------------------

    serial = _texto(
        serial
    )

    if not serial:
        raise RMAError(
            "Serial inválido."
        )

    # --------------------------------------------------------
    # FABRICANTE
    # --------------------------------------------------------

    fabricante = _validar_fabricante(
        fabricante
    )

    # --------------------------------------------------------
    # STARTER
    # --------------------------------------------------------

    started = bool(
        started
    )

    marcador_sim = (
        "X"
        if started
        else " "
    )

    marcador_nao = (
        " "
        if started
        else "X"
    )

    # --------------------------------------------------------
    # NÍVEL
    # --------------------------------------------------------

    try:
        nivel = float(
            nivel
        )
    except (
        TypeError,
        ValueError,
    ):
        nivel = 0

    nivel = max(
        0,
        min(
            100,
            nivel,
        ),
    )

    # --------------------------------------------------------
    # LOTE
    # --------------------------------------------------------

    _ = _texto(
        lote
    )

    # --------------------------------------------------------
    # TEXTOS SEGUROS
    # --------------------------------------------------------

    serial_tspl = _texto_tspl(
        serial
    )

    fabricante_tspl = _texto_tspl(
        fabricante
    )

    # ========================================================
    # LAYOUT 100 x 150 mm
    #
    # 203 DPI aproximadamente:
    #
    # 100 mm -> ~800 dots
    # 150 mm -> ~1200 dots
    #
    # Mantemos margem lateral de 40 dots.
    # ========================================================

    linhas = [

        # ----------------------------------------------------
        # CONFIGURAÇÃO DA MÍDIA
        # ----------------------------------------------------

        "SIZE 100 mm,150 mm",
        "GAP 2 mm,0 mm",
        "REFERENCE 0,0",
        "DIRECTION 1",
        "CLS",

        # ====================================================
        # CABEÇALHO
        # ====================================================

        'TEXT 40,30,"5",0,1,1,"RMA"',
        'BAR 40,105,720,3',

        # ====================================================
        # SERIAL
        # ====================================================

        'TEXT 40,135,"3",0,1,1,"SERIAL:"',

        (
            f'TEXT 40,185,"4",0,1,1,'
            f'"{serial_tspl}"'
        ),

        # ====================================================
        # CÓDIGO DE BARRAS
        # ====================================================

        (
            f'BARCODE 40,260,"128",175,1,0,'
            f'2,2,"{serial_tspl}"'
        ),

        # ====================================================
        # SEPARADOR
        # ====================================================

        'BAR 40,485,720,3',

        # ====================================================
        # INFORMAÇÕES PRINCIPAIS
        # ====================================================

        (
            f'TEXT 40,525,"3",0,1,1,'
            f'"FABRICANTE: {fabricante_tspl}"'
        ),

        (
            f'TEXT 40,600,"3",0,1,1,'
            f'"STARTER: ({marcador_sim}) SIM   '
            f'({marcador_nao}) NAO"'
        ),

        (
            'TEXT 40,675,"3",0,1,1,'
            '"DEFEITO: FALHAS"'
        ),

        (
            f'TEXT 40,750,"3",0,1,1,'
            f'"NIVEL: {nivel:.0f}%"'
        ),

        # ====================================================
        # ÁREA DO LOTE
        # ====================================================

        'BAR 40,815,720,3',

        (
            'TEXT 40,855,"3",0,1,1,'
            '"LOTE:"'
        ),

        (
            'TEXT 40,915,"4",0,1,1,'
            '"________________________________________________"'
        ),

        # ====================================================
        # IMPRESSÃO
        # ====================================================

        "PRINT 1,1",
    ]

    resultado_tspl = (
        "\r\n".join(
            linhas
        )
        + "\r\n"
    )

    _rma_log(
        _t0,
        "SAINDO DE gerar_etiqueta_rma"
    )

    return resultado_tspl


# ============================================================
# IMPRESSÃO RAW NA TSC
# ============================================================

def imprimir_tspl(
    tspl,
    ip=TSC_IP,
    porta=TSC_PORTA,
):
    """
    Envia TSPL diretamente para a TSC.

    Não utiliza o spooler do Windows.
    Não utiliza a UST como destino.
    Não realiza descoberta de impressora.
    """

    _t0 = time.perf_counter()

    _rma_log(
        _t0,
        "ENTROU EM imprimir_tspl"
    )

    if not tspl:
        raise RMAError(
            "TSPL vazio."
        )

    ip = _texto(
        ip,
        TSC_IP,
    )

    try:
        porta = int(
            porta
        )
    except (
        TypeError,
        ValueError,
    ):
        porta = TSC_PORTA

    try:

        _rma_log(
            _t0,
            f"ANTES DE socket.create_connection -> {ip}:{porta}"
        )

        with socket.create_connection(
            (
                ip,
                porta,
            ),
            timeout=10,
        ) as conexao:

            _rma_log(
                _t0,
                "DEPOIS DE socket.create_connection"
            )

            _rma_log(
                _t0,
                "ANTES DE conexao.sendall"
            )

            conexao.sendall(
                tspl.encode(
                    "cp1252",
                    errors="replace",
                )
            )

            _rma_log(
                _t0,
                "DEPOIS DE conexao.sendall — ENVIO CONCLUÍDO"
            )

    except Exception as erro:

        raise RMAError(
            "Não foi possível enviar "
            "a etiqueta RMA para a TSC.\n\n"
            f"TSC: {ip}:{porta}\n\n"
            f"{erro}"
        ) from erro


# ============================================================
# IMPRESSÃO COMPLETA
# ============================================================

def imprimir_rma(
    device,
    fabricante=FABRICANTE_LEXMARK,
    lote="",
):
    """
    Prepara e imprime uma etiqueta RMA.

    Fluxo:

        1. Obtém unidade de imagem.
        2. Obtém serial.
        3. Obtém nível.
        4. Localiza SYSDEBUG salvo, quando necessário.
        5. Localiza bloco da unidade.
        6. Procura AM IU.
        7. Determina Starter.
        8. Gera TSPL.
        9. Envia diretamente para TSC.

    NÃO realiza nova coleta.
    """

    _t0 = time.perf_counter()

    _rma_log(
        _t0,
        "ENTROU EM imprimir_rma"
    )

    dados = preparar_rma(
        device=device,
        fabricante=fabricante,
        lote=lote,
    )

    _rma_log(
        _t0,
        "DEPOIS DE preparar_rma"
    )

    tspl = gerar_etiqueta_rma(
        serial=dados["serial"],
        fabricante=dados["fabricante"],
        started=dados["started"],
        nivel=dados["nivel"],
        lote=dados["lote"],
    )

    _rma_log(
        _t0,
        "DEPOIS DE gerar_etiqueta_rma"
    )

    imprimir_tspl(
        tspl
    )

    _rma_log(
        _t0,
        "DEPOIS DE imprimir_tspl — ETIQUETA ENVIADA"
    )

    return {
        "sucesso": True,
        "relatorio": "rma",
        "destino": "TSC",
        "ip": TSC_IP,
        "porta": TSC_PORTA,
        "largura_mm": ETIQUETA_LARGURA_MM,
        "altura_mm": ETIQUETA_ALTURA_MM,
        "gap_mm": GAP_MM,
        "serial": dados["serial"],
        "fabricante": dados["fabricante"],
        "started": dados["started"],
        "starter": dados["started"],
        "starter_texto": dados["starter_texto"],
        "defeito": dados["defeito"],
        "nivel": dados["nivel"],
        "lote": dados["lote"],
    }


# ============================================================
# INFORMAÇÕES DA RMA
# ============================================================

def informacoes_rma(
    device,
    fabricante=FABRICANTE_LEXMARK,
    lote="",
):
    """
    Prepara as informações da RMA sem imprimir.

    Útil para a interface apresentar uma prévia.

    O Starter é determinado automaticamente pelo SYSDEBUG
    já salvo, com a exceção conhecida do MS622/MS622de.
    """

    dados = preparar_rma(
        device=device,
        fabricante=fabricante,
        lote=lote,
    )

    return {
        "relatorio": "rma",
        "destino": "TSC",
        "ip": TSC_IP,
        "porta": TSC_PORTA,
        "largura_mm": ETIQUETA_LARGURA_MM,
        "altura_mm": ETIQUETA_ALTURA_MM,
        "gap_mm": GAP_MM,
        "serial": dados["serial"],
        "fabricante": dados["fabricante"],
        "started": dados["started"],
        "starter": dados["started"],
        "starter_texto": dados["starter_texto"],
        "defeito": dados["defeito"],
        "nivel": dados["nivel"],
        "lote": dados["lote"],
    }


# ============================================================
# FIM
# ============================================================