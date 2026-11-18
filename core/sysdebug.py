"""
Printer Assistant - SYSDEBUG

Camada de coleta e interpretação dos relatórios SYSDEBUG.

Responsabilidades:

    - acessar /cgi-bin/sysdebugdata
    - acessar /cgi-bin/enginedebugdata quando necessário
    - preservar o relatório bruto
    - identificar fabricante
    - identificar modelo
    - identificar serial da máquina
    - identificar firmware
    - identificar contador
    - extrair consumíveis reconhecíveis
    - extrair seriais reais dos consumíveis

MS622:

    A Lexmark MS622 pode não disponibilizar /cgi-bin/sysdebugdata.

    Nesse caso, utiliza /cgi-bin/enginedebugdata.

    Supply Table:

        Type 2 -> toner
        Type 4 -> unidade_imagem
        Type 5 -> fusor

    Para a MS622:

        stored serial XXXXX

    possui prioridade sobre:

        serial XXXXX valid Y

    O campo "valid" não é utilizado como condição para aceitar
    o stored serial.

    Placeholder conhecido:

        000000000000

    é rejeitado.
"""

import html
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TIMEOUT_SYSDEBUG = 60

SYSDEBUG_ENDPOINT = "/cgi-bin/sysdebugdata"

# Endpoint específico utilizado pela MS622
ENGINE_DEBUG_ENDPOINT = "/cgi-bin/enginedebugdata"

LOG_DIR = (
    Path(__file__).resolve().parent.parent
    / "logs"
    / "sysdebug"
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_html(texto):
    """
    Converte HTML básico em texto para facilitar o parser.
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
        r"</?[a-zA-Z!][^>\r\n]*>",
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


def normalizar_texto(valor):
    """
    Normaliza texto para comparação.
    """

    if valor is None:
        return ""

    texto = str(valor).strip().lower()

    substituicoes = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "ä": "a",
        "é": "e",
        "ê": "e",
        "ë": "e",
        "í": "i",
        "ï": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ö": "o",
        "ú": "u",
        "ü": "u",
        "ç": "c",
        "-": " ",
        "_": " ",
        ".": " ",
    }

    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)

    return " ".join(texto.split())


def valor_limpo(valor):
    """
    Limpa valores extraídos do relatório.
    """

    if valor is None:
        return None

    valor = html.unescape(str(valor))

    valor = re.sub(
        r"</?[a-zA-Z!][^>\r\n]*>",
        " ",
        valor,
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor,
    )

    return valor.strip()


# ============================================================
# LOG DO RELATÓRIO BRUTO
# ============================================================

def salvar_relatorio_bruto(ip, texto, sufixo=""):
    """
    Salva o relatório bruto para diagnóstico futuro.

    O sufixo permite diferenciar:

        sysdebug_...
        sysdebug_..._engine
    """

    agora = datetime.now()

    pasta = (
        LOG_DIR
        / (
            "sysdebug_"
            + ip.replace(".", "_")
            + "_"
            + agora.strftime("%Y%m%d")
        )
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True,
    )

    nome = (
        "sysdebug_"
        + agora.strftime("%H%M%S_%f")
        + sufixo
        + ".html"
    )

    arquivo = pasta / nome

    arquivo.write_text(
        texto,
        encoding="utf-8",
        errors="ignore",
    )

    return arquivo


# ============================================================
# COLETA
# ============================================================

def coletar_sysdebug(ip):
    """
    Coleta informações da impressora.

    Fluxo normal:

        /cgi-bin/sysdebugdata

    Caso o endpoint tradicional retorne HTTP 404:

        /cgi-bin/enginedebugdata

    O segundo caminho é utilizado para impressoras como a MS622.

    IMPORTANTE:

    A lógica tradicional não é substituída.
    """

    if not ip:
        print("[SYSDEBUG] IP não informado.")
        return {}

    # --------------------------------------------------------
    # 1. TENTA SYSDEBUG TRADICIONAL
    # --------------------------------------------------------

    url = f"http://{ip}{SYSDEBUG_ENDPOINT}"

    print(f"[SYSDEBUG] Consultando {url}")

    texto = ""
    status_code = None
    chunks = []

    try:
        # Usa stream=True com timeout de conexão (6s) e timeout entre blocos (4s).
        # Evita travar caso o micro-servidor HTTP da impressora congele no final do dump de ~2.6 MB
        with requests.get(url, stream=True, timeout=(6, 4)) as resp:
            status_code = resp.status_code
            if status_code == 200:
                for chunk in resp.iter_content(chunk_size=32768):
                    chunks.append(chunk)
                texto = b"".join(chunks).decode("utf-8", errors="ignore")
    except requests.RequestException as erro:
        if chunks:
            texto = b"".join(chunks).decode("utf-8", errors="ignore")
            if len(texto) >= 50000:
                print(f"[SYSDEBUG] Stream finalizado com dados capturados ({len(texto)} bytes).")
                status_code = 200
        if not texto:
            print(
                "[SYSDEBUG] Erro de comunicação:",
                erro,
            )
            if hasattr(erro, "response") and erro.response is not None:
                status_code = erro.response.status_code
            else:
                return {}

    except Exception as erro:
        if chunks:
            texto = b"".join(chunks).decode("utf-8", errors="ignore")
            if len(texto) >= 50000:
                print(f"[SYSDEBUG] Stream finalizado com dados capturados ({len(texto)} bytes).")
                status_code = 200
        if not texto:
            print(
                "[SYSDEBUG] Erro inesperado:",
                erro,
            )
            return {}

    # --------------------------------------------------------
    # 2. SYSDEBUG TRADICIONAL FUNCIONOU
    # --------------------------------------------------------

    if status_code == 200:

        if not texto:
            print("[SYSDEBUG] Relatório vazio.")
            return {}

        print(
            "[SYSDEBUG] Relatório recebido:",
            len(texto),
            "bytes",
        )

        try:
            arquivo = salvar_relatorio_bruto(
                ip,
                texto,
            )

            print(
                "[SYSDEBUG] Relatório bruto salvo em:"
            )

            print(arquivo)

        except Exception as erro:
            print(
                "[SYSDEBUG] Não foi possível salvar "
                "relatório bruto:",
                erro,
            )

        # ----------------------------------------------------
        # PARSE TRADICIONAL
        # ----------------------------------------------------

        dados = parse_sysdebug(texto)

        dados["ip"] = ip
        dados["origem"] = "SYSDEBUG"

        print(
            "[SYSDEBUG] Campos encontrados:",
            ", ".join(dados.keys())
            if dados
            else "nenhum",
        )

        # ----------------------------------------------------
        # SE FOR MS622, CONSULTA TAMBÉM ENGINE DEBUG
        # ----------------------------------------------------

        modelo = str(
            dados.get("modelo", "") or ""
        ).strip()

        eh_ms622 = bool(
            re.search(
                r"\bMS\s*622\b",
                modelo,
                re.IGNORECASE,
            )
        )

        if not eh_ms622:
            eh_ms622 = bool(
                re.search(
                    r"\bMS\s*622\b",
                    texto,
                    re.IGNORECASE,
                )
            )

        if eh_ms622:
            return coletar_engine_debug_ms622(
                ip,
                dados,
            )

        return dados

    # --------------------------------------------------------
    # 3. ENDPOINT TRADICIONAL NÃO EXISTE
    #
    # MS622 conhecida neste projeto:
    # /cgi-bin/sysdebugdata -> HTTP 404
    # /cgi-bin/enginedebugdata -> HTTP 200
    # --------------------------------------------------------

    if status_code == 404:

        print(
            "[SYSDEBUG] HTTP 404 no SYSDEBUG tradicional."
        )

        print(
            "[SYSDEBUG] Tentando Engine Debug Data."
        )

        return coletar_engine_debug_ms622(
            ip,
            {},
        )

    # --------------------------------------------------------
    # 4. OUTRO ERRO HTTP
    # --------------------------------------------------------

    print(
        "[SYSDEBUG] HTTP",
        status_code,
        "em",
        url,
    )

    return {}


# ============================================================
# ENGINE DEBUG - MS622
# ============================================================

def coletar_engine_debug_ms622(ip, dados_base=None):
    """
    Coleta o Engine Debug Data.

    Utilizado principalmente pela Lexmark MS622.

    O parser só aceita a estrutura conhecida da Supply Table,
    evitando transformar qualquer número do relatório em
    consumível.
    """

    if dados_base is None:
        dados_base = {}

    url_engine = (
        f"http://{ip}"
        f"{ENGINE_DEBUG_ENDPOINT}"
    )

    print(
        "[SYSDEBUG] Consultando Engine Debug Data:",
        url_engine,
    )

    try:
        resposta_engine = requests.get(
            url_engine,
            timeout=TIMEOUT_SYSDEBUG,
        )

    except requests.RequestException as erro:
        print(
            "[SYSDEBUG] Erro ao consultar "
            "Engine Debug Data:",
            erro,
        )
        return dados_base

    except Exception as erro:
        print(
            "[SYSDEBUG] Erro inesperado no "
            "Engine Debug Data:",
            erro,
        )
        return dados_base

    if resposta_engine.status_code != 200:
        print(
            "[SYSDEBUG] Engine Debug Data HTTP",
            resposta_engine.status_code,
            "em",
            url_engine,
        )
        return dados_base

    texto_engine = resposta_engine.text

    if not texto_engine:
        print(
            "[SYSDEBUG] Engine Debug Data vazio."
        )
        return dados_base

    print(
        "[SYSDEBUG] Engine Debug Data recebido:",
        len(texto_engine),
        "bytes",
    )

    # --------------------------------------------------------
    # SALVA RELATÓRIO ENGINE
    # --------------------------------------------------------

    try:
        arquivo_engine = salvar_relatorio_bruto(
            ip,
            texto_engine,
            "_engine",
        )

        print(
            "[SYSDEBUG] Engine Debug Data bruto salvo em:"
        )

        print(arquivo_engine)

    except Exception as erro:
        print(
            "[SYSDEBUG] Não foi possível salvar "
            "Engine Debug Data bruto:",
            erro,
        )

    # --------------------------------------------------------
    # VERIFICA SE É UMA SUPPLY TABLE RECONHECÍVEL
    # --------------------------------------------------------

    consumiveis_engine = (
        extrair_consumiveis_engine_debug(
            texto_engine
        )
    )

    if not consumiveis_engine:

        print(
            "[SYSDEBUG] Engine Debug Data recebido, "
            "mas nenhuma Supply Table reconhecível foi encontrada."
        )

        return dados_base

    # --------------------------------------------------------
    # MS622 RECONHECIDA
    # --------------------------------------------------------

    dados = dict(dados_base)

    dados["ip"] = ip
    dados["origem"] = "SYSDEBUG"

    # --------------------------------------------------------
    # FIRMWARE
    #
    # MS622 / Engine Debug:
    #
    # RIP Release: MSTGM.076.294, Date: 17-Nov-21 03:04
    #
    # O valor de RIP Release é utilizado como firmware.
    # --------------------------------------------------------

    firmware = extrair_firmware(
        limpar_html(texto_engine)
    )

    if firmware:
        dados["firmware"] = firmware

    # Quando chegamos aqui por HTTP 404, o SYSDEBUG não forneceu
    # o modelo. O modelo normalmente será preenchido pelo PJL
    # posteriormente no PrinterDevice.
    #
    # Não inventamos "MS622" a partir de Speed, Index etc.

    dados["consumiveis"] = consumiveis_engine
    dados["sysdebug_filtered"] = extrair_sysdebug_filtered(
        limpar_html(texto_engine),
        consumiveis_engine,
    )

    print(
        "[SYSDEBUG] Supply Table Engine reconhecida."
    )

    print(
        "[SYSDEBUG] Consumíveis MS622 encontrados:",
        len(consumiveis_engine),
    )

    for supply in consumiveis_engine:

        print(
            "    ",
            supply.get("tipo"),
            "->",
            supply.get("nome"),
            "->",
            supply.get("numero_serie"),
        )

    return dados


# ============================================================
# EXTRAÇÃO DE CAMPO
# ============================================================

def extrair_campo(texto, padroes):
    """
    Tenta vários padrões de campo.
    """

    for padrao in padroes:

        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE,
        )

        if not encontrado:
            continue

        valor = valor_limpo(
            encontrado.group(1)
        )

        if valor:
            return valor

    return None


# ============================================================
# SERIAL DA MÁQUINA
# ============================================================

def extrair_serial_maquina(texto):
    """
    Extrai o serial da própria impressora.

    Esse serial é diferente dos seriais dos consumíveis.
    """

    return extrair_campo(
        texto,
        (
            r"Printer\s+Serial\s+Number\s*[:=]\s*([^\r\n<]+)",
            r"Printer\s+Serial\s+Number\s*;\s*([^\r\n<]+)",
            r"Serial\s+Number\s*[:=]\s*([^\r\n<]+)",
            r"Serial\s+Number\s*;\s*([^\r\n<]+)",
        ),
    )


# ============================================================
# CONTADOR
# ============================================================

def extrair_contador(texto):
    """
    Page Counter possui prioridade.

    Fallback:

        Pg Cnt
    """

    padroes = (
        r"\bPage\s+Counter\s*(?:;|:|=)\s*([0-9][0-9,.\s]*)",
        r"\bPage\s+Counter\s+([0-9][0-9,.\s]*)",
    )

    for padrao in padroes:

        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE,
        )

        if encontrado:

            bruto = encontrado.group(1).strip()

            numero = re.sub(
                r"[^\d]",
                "",
                bruto,
            )

            if numero:

                return (
                    int(numero),
                    "SYSDEBUG Page Counter",
                )

    padroes_fallback = (
        r"\bPg\s+Cnt\s*(?:;|:|=)\s*([0-9][0-9,.\s]*)",
        r"\bPg\s+Cnt\s+([0-9][0-9,.\s]*)",
    )

    for padrao in padroes_fallback:

        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE,
        )

        if encontrado:

            bruto = encontrado.group(1).strip()

            numero = re.sub(
                r"[^\d]",
                "",
                bruto,
            )

            if numero:

                return (
                    int(numero),
                    "SYSDEBUG Pg Cnt",
                )

    return (
        None,
        None,
    )


# ============================================================
# MODELO
# ============================================================

def extrair_modelo(texto):
    """
    Extrai modelo somente de campos conhecidos.

    NÃO utiliza Speed, Index ou valores genéricos como modelo.
    """

    padroes = (
        r"Model\s+Name\s*[:=]\s*([^\r\n<]+)",
        r"Printer\s+Model\s*[:=]\s*([^\r\n<]+)",
        r"Device\s+Model\s*[:=]\s*([^\r\n<]+)",
        r"Product\s+Name\s*[:=]\s*([^\r\n<]+)",
        r"Model\s*[:=]\s*([^\r\n<]+)",
    )

    modelo = extrair_campo(
        texto,
        padroes,
    )

    if modelo:

        normalizado = normalizar_texto(
            modelo
        )

        if normalizado.startswith("speed"):
            modelo = None

    if modelo:
        return modelo.strip()

    # --------------------------------------------------------
    # FALLBACK ESPECÍFICO LEXMARK (APENAS CABEÇALHO/TÍTULO)
    # --------------------------------------------------------
    # Evita buscar no corpo inteiro do HTML, o que causava a captura errônea
    # de modelos de emulação ou compatibilidade citados em logs (ex: MS510 em MX611).
    cabecalho = texto[:3000]
    match_title = re.search(r"<title>\s*([^<]+?)\s*</title>", cabecalho, re.IGNORECASE)
    if match_title:
        title_text = match_title.group(1).strip()
        m = re.search(r"(?:Lexmark\s+)?([A-Z]{2}\s*\d{3}[A-Za-z0-9]*)", title_text, re.IGNORECASE)
        if m:
            return m.group(0).replace(" ", "").upper()

    return None


# ============================================================
# FIRMWARE
# ============================================================

def extrair_firmware(texto):

    # --------------------------------------------------------
    # MS622 / Engine Debug
    #
    # Exemplo:
    #
    # RIP Release: MSTGM.076.294, Date: 17-Nov-21 03:04
    # --------------------------------------------------------

    match_rip = re.search(
        r"RIP\s+Release\s*:\s*([^,\r\n<]+)",
        texto,
        re.IGNORECASE,
    )

    if match_rip:

        valor = match_rip.group(1).strip()

        if valor:
            return valor

    # --------------------------------------------------------
    # Formatos tradicionais
    # --------------------------------------------------------

    padroes = (
        (
            r"RIP\s+Firmware\s+Version"
            r"[^\n]*\n\s*([^\r\n<]+)"
        ),
        (
            r"Firmware\s+Version"
            r"\s*[:=]\s*([^\r\n<]+)"
        ),
        (
            r"Firmware"
            r"\s*[:=]\s*([^\r\n<]+)"
        ),
    )

    valor = extrair_campo(
        texto,
        padroes,
    )

    if not valor:
        return None

    if normalizar_texto(
        valor
    ).startswith("speed"):
        return None

    return valor.strip()


# ============================================================
# FABRICANTE
# ============================================================

def extrair_fabricante(texto):

    texto_normalizado = normalizar_texto(
        texto
    )

    fabricantes = (
        ("lexmark", "Lexmark"),
        ("brother", "Brother"),
        ("epson", "Epson"),
        ("canon", "Canon"),
        ("hewlett packard", "HP"),
        ("hp", "HP"),
    )

    for chave, nome in fabricantes:

        if chave in texto_normalizado:
            return nome

    return None


# ============================================================
# TIPO DE CONSUMÍVEL
# ============================================================

def tipo_consumivel(nome):

    texto = normalizar_texto(
        nome
    )

    if (
        "toner" in texto
        or "cartucho" in texto
        or "cartridge" in texto
    ):
        return "toner"

    if (
        "imagem" in texto
        or "imaging" in texto
        or "photoconductor" in texto
        or "fotocondutor" in texto
        or "drum" in texto
    ):
        return "unidade_imagem"

    if (
        "fusor" in texto
        or "fuser" in texto
        or "maintenance" in texto
        or "manuten" in texto
    ):
        return "fusor"

    return ""


# ============================================================
# CONSUMÍVEIS - ENGINE DEBUG MS622
# ============================================================

def extrair_consumiveis_engine_debug(texto):
    """
    Parser específico do Engine Debug Data da Lexmark MS622.

    Mantém a Supply Table como fonte de identidade e nível,
    usando as seções detalhadas para métricas adicionais.
    """

    consumiveis = []

    if not texto:
        return consumiveis

    texto_limpo = limpar_html(texto)

    if not texto_limpo:
        return consumiveis

    # --------------------------------------------------------
    # SUPPLY TABLE
    # --------------------------------------------------------

    padrao_supply = re.compile(
        r"supply\s*=\s*\d+\s*,\s*"
        r"\(([^)]+)\)\s*,"
        r"(.*?)"
        r"(?=\n\s*supply\s*=\s*\d+\s*,\s*\(|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    for encontrado in padrao_supply.finditer(
        texto_limpo
    ):

        nome = valor_limpo(
            encontrado.group(1)
        )

        bloco = encontrado.group(2)

        if not nome:
            continue

        # ----------------------------------------------------
        # TIPO
        # ----------------------------------------------------

        tipo = None

        encontrado_type = re.search(
            r"\bType\s+(\d+)\b",
            bloco,
            re.IGNORECASE,
        )

        if encontrado_type:

            codigo_tipo = encontrado_type.group(1)

            if codigo_tipo == "2":
                tipo = "toner"

            elif codigo_tipo == "4":
                tipo = "unidade_imagem"

            elif codigo_tipo == "5":
                tipo = "fusor"

        if tipo is None:

            tipo_nome = tipo_consumivel(
                nome
            )

            if tipo_nome:
                tipo = tipo_nome

        if tipo is None:
            continue

        # ----------------------------------------------------
        # SERIAL REAL DA SUPPLY TABLE
        # ----------------------------------------------------

        numero_serie = None

        encontrado_stored = re.search(
            r"\bstored\s+serial\s+"
            r"([A-Za-z0-9][A-Za-z0-9_-]*)",
            bloco,
            re.IGNORECASE,
        )

        if encontrado_stored:

            numero_serie = valor_limpo(
                encontrado_stored.group(1)
            )

        if not numero_serie:

            encontrado_serial = re.search(
                r"\bserial\s+"
                r"([A-Za-z0-9][A-Za-z0-9_-]*)"
                r"\s+valid\s+\d+",
                bloco,
                re.IGNORECASE,
            )

            if encontrado_serial:

                numero_serie = valor_limpo(
                    encontrado_serial.group(1)
                )

        if numero_serie and re.fullmatch(
            r"0+",
            numero_serie,
        ):
            numero_serie = None

        # ----------------------------------------------------
        # PART NUMBER
        # ----------------------------------------------------

        part_number = None

        encontrado_part = re.search(
            r"\bpart\s+number\s+"
            r"([^,\r\n]*)",
            bloco,
            re.IGNORECASE,
        )

        if encontrado_part:

            part_number = valor_limpo(
                encontrado_part.group(1)
            )

            if not part_number:
                part_number = None

        # ----------------------------------------------------
        # NÍVEL + CONDIÇÃO
        # ----------------------------------------------------

        nivel = None
        condicao = None

        encontrado_nivel = re.search(
            r"\bLevel\s+(\d+)\s*,\s*"
            r"Current\s+Status\s+([A-Za-z]+)",
            bloco,
            re.IGNORECASE,
        )

        if encontrado_nivel:

            nivel = int(
                encontrado_nivel.group(1)
            )

            condicao = valor_limpo(
                encontrado_nivel.group(2)
            )

        # ----------------------------------------------------
        # SEÇÃO DETALHADA
        # ----------------------------------------------------

        detalhe = ""

        if tipo == "toner":

            encontrado_detalhe = re.search(
                r"/proc/supplies/bottle"
                r"(.*?)(?=/proc/supplies/fuser)",
                texto_limpo,
                re.IGNORECASE | re.DOTALL,
            )

        elif tipo == "fusor":

            encontrado_detalhe = re.search(
                r"/proc/supplies/fuser"
                r"(.*?)(?=/proc/supplies/iu)",
                texto_limpo,
                re.IGNORECASE | re.DOTALL,
            )

        elif tipo == "unidade_imagem":

            encontrado_detalhe = re.search(
                r"/proc/supplies/iu"
                r"(.*?)(?=/proc/supplies/nlrp)",
                texto_limpo,
                re.IGNORECASE | re.DOTALL,
            )

        else:

            encontrado_detalhe = None

        if encontrado_detalhe:
            detalhe = encontrado_detalhe.group(1)

        # ----------------------------------------------------
        # CAPACIDADE
        # ----------------------------------------------------

        capacidade = None

        encontrado_capacidade = re.search(
            r"\bmaxCapacityPages\s+(\d+)",
            bloco,
            re.IGNORECASE,
        )

        if encontrado_capacidade:

            capacidade = int(
                encontrado_capacidade.group(1)
            )

        # ----------------------------------------------------
        # RESTANTE
        # ----------------------------------------------------

        restante = None

        encontrado_restante = re.search(
            r"\bReportedPgsRemaining\s*[:=]\s*(\d+)",
            detalhe,
            re.IGNORECASE,
        )

        if encontrado_restante:

            restante = int(
                encontrado_restante.group(1)
            )

        if restante is None:

            encontrado_restante = re.search(
                r"\bReportPgsRem\s*:\s*(\d+)",
                detalhe,
                re.IGNORECASE,
            )

            if encontrado_restante:

                restante = int(
                    encontrado_restante.group(1)
                )

        # --------------------------------------------------------
        # FALLBACK DO FUSOR
        #
        # O Engine Debug coloca o valor do fusor no resumo
        # identificado explicitamente por:
        #
        #     PrinterSerNo in fuser:
        #     ReportedPgsRemaining=123200
        #
        # Procuramos essa identificação para não capturar
        # valores de toner ou unidade de imagem.
        # --------------------------------------------------------

        if restante is None and tipo == "fusor":

            encontrado_restante = re.search(
                r"PrinterSerNo\s+in\s+fuser\s*:.*?"
                r"\bReportedPgsRemaining\s*=\s*(\d+)",
                texto_limpo,
                re.IGNORECASE | re.DOTALL,
            )

            if encontrado_restante:

                restante = int(
                    encontrado_restante.group(1)
                )

        # ----------------------------------------------------
        # SIDE COUNT
        # ----------------------------------------------------

        side_count = None

        encontrado_side = re.search(
            r"\bSideCount\s*(?:=|:)\s*(\d+)",
            detalhe,
            re.IGNORECASE,
        )

        if encontrado_side:

            side_count = int(
                encontrado_side.group(1)
            )

        # ----------------------------------------------------
        # DIAS RESTANTES
        # ----------------------------------------------------

        dias_restantes = None

        encontrado_dias = re.search(
            r"\bReportedDaysRemaining\s*=?\s*(\d+)",
            detalhe,
            re.IGNORECASE,
        )

        if encontrado_dias:

            dias_restantes = int(
                encontrado_dias.group(1)
            )

        if dias_restantes is None:

            encontrado_dias = re.search(
                r"\bDaysRem\s*:\s*(\d+)",
                detalhe,
                re.IGNORECASE,
            )

            if encontrado_dias:

                dias_restantes = int(
                    encontrado_dias.group(1)
                )

        # ----------------------------------------------------
        # NÍVEL ESPECÍFICO
        # ----------------------------------------------------

        if tipo in ("toner", "fusor"):

            encontrado_nivel_detalhe = re.search(
                r"\bCurrentReportedLevel\s*=\s*(\d+)",
                detalhe,
                re.IGNORECASE,
            )

        elif tipo == "unidade_imagem":

            encontrado_nivel_detalhe = re.search(
                r"\bPercent\s+Remaining\s*=\s*(\d+)",
                detalhe,
                re.IGNORECASE,
            )

        else:

            encontrado_nivel_detalhe = None

        if encontrado_nivel_detalhe:

            nivel = int(
                encontrado_nivel_detalhe.group(1)
            )

        # ----------------------------------------------------
        # CONSUMIDO
        # ----------------------------------------------------

        consumido = None

        # Para o fusor, SideCount é o contador real de lados
        # consumidos.

        if tipo == "fusor" and side_count is not None:

            consumido = side_count

        # Para os demais, se não houver contador explícito,
        # usamos capacidade - restante.

        elif (
            capacidade is not None
            and restante is not None
            and restante <= capacidade
        ):

            consumido = capacidade - restante

        # ----------------------------------------------------
        # REGISTRO NORMALIZADO
        # ----------------------------------------------------

        consumiveis.append(
            {
                "tipo": tipo,
                "nome": nome,
                "numero_serie": numero_serie,
                "part_number": part_number,
                "percentual": nivel,
                "nivel": nivel,
                "condicao": condicao or "N/D",
                "capacidade": capacidade,
                "restante": restante,
                "consumido": consumido,
                "side_count": side_count,
                "dias_restantes": dias_restantes,
            }
        )

    return consumiveis


# ============================================================
# CONSUMÍVEIS - SYSDEBUG TRADICIONAL
# ============================================================

def extrair_consumiveis_sysdebug(texto):
    """
    Extrai consumíveis reais dos blocos conhecidos
    do SYSDEBUG tradicional.

    A lógica tradicional permanece separada da MS622.
    """

    consumiveis = []

    if not texto:
        return consumiveis

    texto_limpo = limpar_html(texto)

    # ========================================================
    # UNIDADE DE IMAGEM
    # ========================================================

    serial_imaging = None
    part_imaging = None

    padrao_imaging = re.compile(
        r"Mono\s+Cartridge\s+Imaging\s+Unit"
        r".{0,1500}?"
        r"S/N\s*:\s*"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)",
        re.IGNORECASE | re.DOTALL,
    )

    encontrado = padrao_imaging.search(
        texto_limpo
    )

    if encontrado:

        serial_candidato = valor_limpo(
            encontrado.group(1)
        )

        if (
            serial_candidato
            and not re.fullmatch(r"0+", serial_candidato)
        ):
            serial_imaging = serial_candidato

    # Fallback 1: ST Supply Table Data (osikey Imaging Unit)
    padrao_osikey_imaging = re.compile(
        r"osikey\s+(?:Black\s+)?Imaging\s+Unit\s*,\s*serial\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)"
        r"\s+valid\s+\d+"
        r"(.*?)"
        r"(?=osikey\s+|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    encontrado_osikey_iu = padrao_osikey_imaging.search(
        texto_limpo
    )

    if encontrado_osikey_iu:
        serial_iu_osikey = valor_limpo(encontrado_osikey_iu.group(1))
        bloco_iu_osikey = encontrado_osikey_iu.group(2)
        match_pn_iu = re.search(
            r"\bpartNumber\s+([A-Za-z0-9_-]+)",
            bloco_iu_osikey,
            re.IGNORECASE,
        )
        if match_pn_iu:
            part_imaging = valor_limpo(match_pn_iu.group(1))

        if (
            not serial_imaging
            and serial_iu_osikey
            and not re.fullmatch(r"0+", serial_iu_osikey)
        ):
            serial_imaging = serial_iu_osikey

    # Fallback 2: Key=Imaging Unit, Value=Map
    if not serial_imaging:
        padrao_map_imaging = re.compile(
            r"Key=Imaging\s+Unit,\s*Value=Map"
            r"(.*?)"
            r"(?=Key=Maintenance\s+Kit,\s*Value=Map|"
            r"Key=Fuser,\s*Value=Map|"
            r"End\s+of\s+Dump|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        encontrado_map_iu = padrao_map_imaging.search(texto_limpo)
        if encontrado_map_iu:
            bloco_map_iu = encontrado_map_iu.group(1)
            match_sn_iu = re.search(
                r'Key=serialNumber,\s*Value="([^"]*)"',
                bloco_map_iu,
                re.IGNORECASE,
            )
            if match_sn_iu:
                cand_iu = valor_limpo(match_sn_iu.group(1))
                if cand_iu and not re.fullmatch(r"0+", cand_iu):
                    serial_imaging = cand_iu

    if serial_imaging:

        item_imaging = {
            "tipo": "unidade_imagem",
            "nome": "Mono Cartridge Imaging Unit",
            "numero_serie": serial_imaging,
        }
        if part_imaging:
            item_imaging["part_number"] = part_imaging

        # Métricas reais de consumo da Unidade de Imagem / Cilindro (Drum)
        m_mono_iu = re.search(
            r"Mono\s+Cartridge\s+Imaging\s+Unit(.*?)(?=Bottle-K|Imaging\s+Unit-K|ST\s+Supply\s+Table|\Z)",
            texto_limpo,
            re.IGNORECASE | re.DOTALL,
        )
        if m_mono_iu:
            b_iu = m_mono_iu.group(1)
            m_pg = re.search(r"IU\s+Page\s+Count\s*[;:=]\s*(\d+)", b_iu, re.IGNORECASE)
            if m_pg:
                item_imaging["page_count"] = int(m_pg.group(1))
                item_imaging["consumido"] = int(m_pg.group(1))
            m_rev = re.search(r"IU\s+PC\s+Drum\s+Rev\s+Count\s*[;:=]\s*(\d+)", b_iu, re.IGNORECASE)
            if m_rev:
                item_imaging["rotations"] = int(m_rev.group(1))
                item_imaging["rotacoes"] = int(m_rev.group(1))
            m_lvl = re.search(r"Current\s+Level\s*=\s*(\d+)", b_iu, re.IGNORECASE)
            if m_lvl:
                item_imaging["nivel"] = int(m_lvl.group(1))
                item_imaging["percentual"] = int(m_lvl.group(1))

        if encontrado_osikey_iu:
            b_osi_iu = encontrado_osikey_iu.group(2)
            m_pg_osi = re.search(r"\bpageCount\s+(\d+)", b_osi_iu, re.IGNORECASE)
            if m_pg_osi and "page_count" not in item_imaging:
                item_imaging["page_count"] = int(m_pg_osi.group(1))
                item_imaging["consumido"] = int(m_pg_osi.group(1))
            m_rem_osi = re.search(r"\bpageRemain\s+(\d+)", b_osi_iu, re.IGNORECASE)
            if m_rem_osi:
                item_imaging["restante"] = int(m_rem_osi.group(1))
            m_max_osi = re.search(r"\bmaxCapacity(?:Pages)?\s+(\d+)", b_osi_iu, re.IGNORECASE)
            if m_max_osi:
                item_imaging["capacidade"] = int(m_max_osi.group(1))
            m_lvl_osi = re.search(r"\blevel\s+(\d+)", b_osi_iu, re.IGNORECASE)
            if m_lvl_osi and "nivel" not in item_imaging:
                item_imaging["nivel"] = int(m_lvl_osi.group(1))
                item_imaging["percentual"] = int(m_lvl_osi.group(1))

        consumiveis.append(item_imaging)

    # ========================================================
    # TONER
    # ========================================================

    serial_toner = None
    part_toner = None

    padrao_black_toner = re.compile(
        r"Key=Black\s+Toner,\s*Value=Map"
        r"(.*?)"
        r"(?=Key=Imaging\s+Unit,\s*Value=Map|"
        r"Key=Maintenance\s+Kit,\s*Value=Map|"
        r"Key=Fuser,\s*Value=Map|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    encontrado_toner = (
        padrao_black_toner.search(
            texto_limpo
        )
    )

    if encontrado_toner:

        bloco_toner = (
            encontrado_toner.group(1)
        )

        encontrado_serial = re.search(
            r'Key=serialNumber,\s*Value="([^"]*)"',
            bloco_toner,
            re.IGNORECASE,
        )

        encontrado_part_number = re.search(
            r'Key=partNumber,\s*Value="([^"]*)"',
            bloco_toner,
            re.IGNORECASE,
        )

        serial = (
            valor_limpo(
                encontrado_serial.group(1)
            )
            if encontrado_serial
            else None
        )

        part_number = (
            valor_limpo(
                encontrado_part_number.group(1)
            )
            if encontrado_part_number
            else None
        )

        if part_number:
            part_toner = part_number

        if (
            serial
            and not re.fullmatch(
                r"0+",
                serial,
            )
        ):
            serial_toner = serial

    # Fallback 1: ST Supply Table Data (osikey Black Toner / Cartridge)
    padrao_osikey_toner = re.compile(
        r"osikey\s+(?:Black\s+)?(?:Toner|Cartridge)\s*,\s*serial\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)"
        r"\s+valid\s+\d+"
        r"(.*?)"
        r"(?=osikey\s+|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    encontrado_osikey_toner = padrao_osikey_toner.search(
        texto_limpo
    )

    if encontrado_osikey_toner:
        serial_osikey = valor_limpo(encontrado_osikey_toner.group(1))
        bloco_osikey = encontrado_osikey_toner.group(2)
        match_pn_osikey = re.search(
            r"\bpartNumber\s+([A-Za-z0-9_-]+)",
            bloco_osikey,
            re.IGNORECASE,
        )
        if not part_toner and match_pn_osikey:
            part_toner = valor_limpo(match_pn_osikey.group(1))

        if (
            not serial_toner
            and serial_osikey
            and not re.fullmatch(r"0+", serial_osikey)
        ):
            serial_toner = serial_osikey

    # Fallback 2: Mono Cartridge Toner Bottle ... S/N:
    if not serial_toner:
        padrao_mono_toner = re.compile(
            r"Mono\s+Cartridge\s+Toner\s+Bottle"
            r"(.*?)"
            r"(?=Mono\s+Cartridge\s+Imaging\s+Unit|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        encontrado_mono_toner = padrao_mono_toner.search(texto_limpo)
        if encontrado_mono_toner:
            match_sn_mono = re.search(
                r"S/N\s*:\s*([A-Za-z0-9][A-Za-z0-9_-]*)",
                encontrado_mono_toner.group(1),
                re.IGNORECASE,
            )
            if match_sn_mono:
                cand_mono = valor_limpo(match_sn_mono.group(1))
                if (
                    cand_mono
                    and len(cand_mono) >= 5
                    and not re.fullmatch(r"0+", cand_mono)
                ):
                    serial_toner = cand_mono

    if serial_toner:

        item_toner = {
            "tipo": "toner",
            "nome": "Black Toner",
            "numero_serie": serial_toner,
            "part_number": part_toner,
        }

        # Métricas reais de consumo do Toner (cartucho)
        m_mono_toner = re.search(
            r"Mono\s+Cartridge\s+Toner\s+Bottle(.*?)(?=Mono\s+Cartridge\s+Imaging\s+Unit|\Z)",
            texto_limpo,
            re.IGNORECASE | re.DOTALL,
        )
        if m_mono_toner:
            b_tb = m_mono_toner.group(1)
            m_pg = re.search(r"Bottle\s+Page\s+Count\s*[:=;]\s*(\d+)", b_tb, re.IGNORECASE)
            if m_pg:
                item_toner["page_count"] = int(m_pg.group(1))
                item_toner["consumido"] = int(m_pg.group(1))
            m_lvl = re.search(r"Current\s+Level\s*=\s*(\d+)", b_tb, re.IGNORECASE)
            if m_lvl:
                item_toner["nivel"] = int(m_lvl.group(1))
                item_toner["percentual"] = int(m_lvl.group(1))

        if encontrado_osikey_toner:
            b_osi_t = encontrado_osikey_toner.group(2)
            m_pg_osi = re.search(r"\bpageCount\s+(\d+)", b_osi_t, re.IGNORECASE)
            if m_pg_osi and "page_count" not in item_toner:
                item_toner["page_count"] = int(m_pg_osi.group(1))
                item_toner["consumido"] = int(m_pg_osi.group(1))
            m_rem = re.search(r"\bpageRemain\s+(\d+)", b_osi_t, re.IGNORECASE)
            if m_rem:
                item_toner["restante"] = int(m_rem.group(1))
            m_cap = re.search(r"\bmaxCapacity(?:Pages)?\s+(\d+)", b_osi_t, re.IGNORECASE)
            if m_cap:
                item_toner["capacidade"] = int(m_cap.group(1))
            m_lvl_osi = re.search(r"\blevel\s+(\d+)", b_osi_t, re.IGNORECASE)
            if m_lvl_osi and "nivel" not in item_toner:
                item_toner["nivel"] = int(m_lvl_osi.group(1))
                item_toner["percentual"] = int(m_lvl_osi.group(1))

        consumiveis.append(item_toner)

    # ========================================================
    # FUSOR / MAINTENANCE KIT
    # ========================================================

    # Regra tradicional preservada:
    #
    # valid 1
    # serialNumberIsReal 1
    #
    # A MS622 NÃO passa por esta regra.

    padrao_maintenance = re.compile(
        r"osikey\s+"
        r"(Maintenance\s+Kit|Fuser|Kit\s+Maintenance)"
        r"\s*,\s*serial\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)"
        r"\s+valid\s+1"
        r".{0,2500}?"
        r"serialNumberIsReal\s+1",
        re.IGNORECASE | re.DOTALL,
    )

    fusor_adicionado = False
    for encontrado in padrao_maintenance.finditer(
        texto_limpo
    ):

        nome = valor_limpo(
            encontrado.group(1)
        )

        serial = valor_limpo(
            encontrado.group(2)
        )

        if not serial:
            continue

        if re.fullmatch(
            r"0+",
            serial,
        ):
            continue

        consumiveis.append(
            {
                "tipo": "fusor",
                "nome": nome or "Maintenance Kit",
                "numero_serie": serial,
                "part_number": None,
            }
        )
        fusor_adicionado = True

    # Métricas de consumo do Fusor / Maintenance Kit (ST Supply Table)
    padrao_fusor_metricas = re.compile(
        r"osikey\s+(?:Maintenance\s+Kit|Fuser|Kit\s+Maintenance)\s*,\s*serial\s+([A-Za-z0-9_-]*)\s+valid\s+\d+(.*?)(?=osikey\s+|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    m_fus = padrao_fusor_metricas.search(texto_limpo)
    if m_fus:
        b_fus = m_fus.group(2)
        item_fusor = {
            "tipo": "fusor",
            "nome": "Maintenance Kit",
            "numero_serie": None,
            "part_number": None,
        }
        m_pg = re.search(r"\bpageCount\s+(\d+)", b_fus, re.IGNORECASE)
        if m_pg:
            item_fusor["page_count"] = int(m_pg.group(1))
            item_fusor["consumido"] = int(m_pg.group(1))
        m_cap = re.search(r"\bmaxCapacity(?:Pages)?\s+(\d+)", b_fus, re.IGNORECASE)
        if m_cap:
            item_fusor["capacidade"] = int(m_cap.group(1))
        m_lvl = re.search(r"\blevel\s+(\d+)", b_fus, re.IGNORECASE)
        if m_lvl:
            item_fusor["nivel"] = int(m_lvl.group(1))
            item_fusor["percentual"] = int(m_lvl.group(1))
        if item_fusor.get("capacidade") and item_fusor.get("consumido") is not None:
            item_fusor["restante"] = max(0, item_fusor["capacidade"] - item_fusor["consumido"])
        if not fusor_adicionado:
            consumiveis.append(item_fusor)
        else:
            # Atualiza o fusor já adicionado
            for f_item in consumiveis:
                if f_item.get("tipo") == "fusor":
                    f_item.update({k: v for k, v in item_fusor.items() if v is not None and k != "numero_serie"})

    return consumiveis


# ============================================================
# SYSDEBUG FILTERED (MÉTRICAS DA UNIDADE DE IMAGEM / DRUM)
# ============================================================

def _decodificar_data_serial_lexmark(serial):
    """
    Decodifica a data gravada no chip de suprimento Lexmark (formato CAxYYDDDxxxx):
    - YY: Ano (20YY)
    - DDD: Dia juliano do ano (001 a 366)
    Retorna string DD/MM/YYYY quando reconhecido.
    """
    if not serial:
        return None
    s = str(serial).strip().upper()
    m = re.match(r"^[A-Z]{3}(\d{2})(\d{3})", s)
    if not m:
        return None
    try:
        yy = int(m.group(1))
        ddd = int(m.group(2))
        ano = 2000 + yy
        if 2000 <= ano <= 2099 and 1 <= ddd <= 366:
            dt = datetime(ano, 1, 1) + timedelta(days=ddd - 1)
            return dt.strftime("%d/%m/%Y")
    except Exception:
        pass
    return None


def extrair_sysdebug_filtered(texto_limpo, consumiveis=None):
    """
    Extrai as métricas exclusivas do chip da Unidade de Imagem (Fotocondutor / Drum)
    diretamente do relatório SYSDEBUG / Engine Debug, sem misturar com o contador
    geral da impressora.
    """
    filtrado = {}
    if not texto_limpo:
        return filtrado

    # 1. Bloco Mono Cartridge Imaging Unit
    match_mono_iu = re.search(
        r"Mono\s+Cartridge\s+Imaging\s+Unit(.*?)(?=Bottle-K\s+status|Imaging\s+Unit-K\s+status|ST\s+Supply\s+Table|Key=Black\s+Toner|\Z)",
        texto_limpo,
        re.IGNORECASE | re.DOTALL,
    )
    if match_mono_iu:
        bloco_iu = match_mono_iu.group(1)

        m_sn = re.search(r"S/N\s*:\s*([A-Za-z0-9][A-Za-z0-9_-]*)", bloco_iu, re.IGNORECASE)
        if m_sn:
            sn = valor_limpo(m_sn.group(1))
            if sn and not re.fullmatch(r"0+", sn):
                filtrado["drum_serial"] = sn

        m_chip = re.search(r"Chip\s+ID\s*:\s*([0-9a-fA-F]+)", bloco_iu, re.IGNORECASE)
        if m_chip:
            filtrado["drum_chip_id"] = valor_limpo(m_chip.group(1))

        m_ec = re.search(r"Chip\s+EC\s+Lvl\s*:\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_ec:
            filtrado["drum_chip_ec_level"] = int(m_ec.group(1))

        m_ttc = re.search(r"TonerToCleaner\s*=\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_ttc:
            filtrado["drum_toner_to_cleaner"] = int(m_ttc.group(1))

        m_ftd = re.search(r"FilteredTnrInDvlpr\s*=\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_ftd:
            filtrado["drum_filtered_toner_dvlpr"] = int(m_ftd.group(1))

        m_pg = re.search(r"IU\s+Page\s+Count\s*[;:=]\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_pg:
            filtrado["drum_page_count"] = int(m_pg.group(1))

        m_rev = re.search(r"IU\s+PC\s+Drum\s+Rev\s+Count\s*[;:=]\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_rev:
            filtrado["drum_rotations"] = int(m_rev.group(1))

        m_urev = re.search(r"IU\s+Unscaled\s+PC\s+Drum\s+Rev\s+Count\s*[;:=]\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_urev:
            filtrado["pc_unscaled_rotations"] = int(m_urev.group(1))

        m_por_sides = re.search(r"SidesPrintedSincePor\s*=\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_por_sides:
            filtrado["pc_sides_since_por"] = int(m_por_sides.group(1))

        m_por_revs = re.search(r"PcDrumRevsSincePor\s*=\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_por_revs:
            filtrado["pc_rotations_since_por"] = int(m_por_revs.group(1))

        m_lvl = re.search(r"Current\s+Level\s*=\s*(\d+)", bloco_iu, re.IGNORECASE)
        if m_lvl:
            filtrado["drum_life_remaining"] = int(m_lvl.group(1))

    # 2. Bloco ST Supply Table Data (osikey Imaging Unit)
    match_osikey_iu = re.search(
        r"osikey\s+(?:Black\s+)?Imaging\s+Unit\s*,\s*serial\s*([A-Za-z0-9_-]*)\s+valid\s+\d+(.*?)(?=osikey\s+|\Z)",
        texto_limpo,
        re.IGNORECASE | re.DOTALL,
    )
    if match_osikey_iu:
        sn_osi = valor_limpo(match_osikey_iu.group(1))
        bloco_osi = match_osikey_iu.group(2)
        if sn_osi and not re.fullmatch(r"0+", sn_osi) and "drum_serial" not in filtrado:
            filtrado["drum_serial"] = sn_osi

        m_pn = re.search(r"\bpartNumber\s+([A-Za-z0-9_-]+)", bloco_osi, re.IGNORECASE)
        if m_pn:
            filtrado["drum_part_number"] = valor_limpo(m_pn.group(1))

        m_pg_osi = re.search(r"\bpageCount\s+(\d+)", bloco_osi, re.IGNORECASE)
        if m_pg_osi and "drum_page_count" not in filtrado:
            filtrado["drum_page_count"] = int(m_pg_osi.group(1))

        m_rem_osi = re.search(r"\bpageRemain\s+(\d+)", bloco_osi, re.IGNORECASE)
        if m_rem_osi:
            filtrado["drum_pages_remaining"] = int(m_rem_osi.group(1))

        m_max_osi = re.search(r"\bmaxCapacityPages\s+(\d+)", bloco_osi, re.IGNORECASE)
        if m_max_osi:
            filtrado["drum_max_capacity"] = int(m_max_osi.group(1))

        m_lvl_osi = re.search(r"\blevel\s+(\d+)", bloco_osi, re.IGNORECASE)
        if m_lvl_osi and "drum_life_remaining" not in filtrado:
            filtrado["drum_life_remaining"] = int(m_lvl_osi.group(1))

    # 3. Bloco Key=Imaging Unit, Value=Map
    match_map_iu = re.search(
        r"Key=Imaging\s+Unit,\s*Value=Map(.*?)(?=Key=Maintenance\s+Kit,\s*Value=Map|Key=Fuser,\s*Value=Map|End\s+of\s+Dump|\Z)",
        texto_limpo,
        re.IGNORECASE | re.DOTALL,
    )
    if match_map_iu:
        bloco_map = match_map_iu.group(1)
        m_sn_map = re.search(r'Key=serialNumber,\s*Value="([^"]*)"', bloco_map, re.IGNORECASE)
        if m_sn_map and "drum_serial" not in filtrado:
            sn_m = valor_limpo(m_sn_map.group(1))
            if sn_m and not re.fullmatch(r"0+", sn_m):
                filtrado["drum_serial"] = sn_m

        m_pn_map = re.search(r'Key=partNumber,\s*Value="([^"]*)"', bloco_map, re.IGNORECASE)
        if m_pn_map and "drum_part_number" not in filtrado:
            pn_m = valor_limpo(m_pn_map.group(1))
            if pn_m:
                filtrado["drum_part_number"] = pn_m

        m_pg_map = re.search(r"Key=pageCount,\s*Value=(\d+)", bloco_map, re.IGNORECASE)
        if m_pg_map and "drum_page_count" not in filtrado:
            filtrado["drum_page_count"] = int(m_pg_map.group(1))

        m_rem_map = re.search(r"Key=pagesRemaining,\s*Value=(\d+)", bloco_map, re.IGNORECASE)
        if m_rem_map and "drum_pages_remaining" not in filtrado:
            filtrado["drum_pages_remaining"] = int(m_rem_map.group(1))

        m_max_map = re.search(r"Key=maxCapacityPages,\s*Value=(\d+)", bloco_map, re.IGNORECASE)
        if m_max_map and "drum_max_capacity" not in filtrado:
            filtrado["drum_max_capacity"] = int(m_max_map.group(1))

        m_lvl_map = re.search(r"Key=percentFull(?:ADS|-INTERNAL-ONLY)?,\s*Value=(\d+)", bloco_map, re.IGNORECASE)
        if m_lvl_map and "drum_life_remaining" not in filtrado:
            filtrado["drum_life_remaining"] = int(m_lvl_map.group(1))

    # 4. Complemento com itens de unidade_imagem extraídos (ex: MS622 Engine Debug)
    if isinstance(consumiveis, list):
        for item in consumiveis:
            if isinstance(item, dict) and item.get("tipo") == "unidade_imagem":
                if item.get("numero_serie") and "drum_serial" not in filtrado:
                    filtrado["drum_serial"] = item["numero_serie"]
                if item.get("part_number") and "drum_part_number" not in filtrado:
                    filtrado["drum_part_number"] = item["part_number"]
                if item.get("side_count") is not None and "drum_page_count" not in filtrado:
                    filtrado["drum_page_count"] = item["side_count"]
                elif item.get("consumido") is not None and "drum_page_count" not in filtrado:
                    filtrado["drum_page_count"] = item["consumido"]
                if item.get("nivel") is not None and "drum_life_remaining" not in filtrado:
                    filtrado["drum_life_remaining"] = item["nivel"]
                if item.get("restante") is not None and "drum_pages_remaining" not in filtrado:
                    filtrado["drum_pages_remaining"] = item["restante"]
                if item.get("capacidade") is not None and "drum_max_capacity" not in filtrado:
                    filtrado["drum_max_capacity"] = item["capacidade"]
                if item.get("dias_restantes") is not None:
                    filtrado["drum_days_remaining"] = item["dias_restantes"]

    # 5. Data de instalação / data do chip do cilindro
    m_inst = re.search(
        r"(?:IU|Drum|Imaging\s+Unit|Photoconductor)?\s*(?:First\s+)?Install(?:ation)?\s*Date\s*[:=]\s*([0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4})",
        texto_limpo,
        re.IGNORECASE,
    )
    if m_inst:
        filtrado["drum_install_date"] = valor_limpo(m_inst.group(1))
    elif filtrado.get("drum_serial"):
        data_serial = _decodificar_data_serial_lexmark(filtrado["drum_serial"])
        if data_serial:
            filtrado["drum_install_date"] = data_serial

    # 6. Métricas do Cartucho de Toner
    # 6.1 Mono Cartridge Toner Bottle
    m_bottle = re.search(
        r"Mono\s+Cartridge\s+Toner\s+Bottle(.*?)(?=Mono\s+Cartridge\s+Imaging\s+Unit|\Z)",
        texto_limpo,
        re.IGNORECASE | re.DOTALL,
    )
    if m_bottle:
        b_tb = m_bottle.group(1)
        m_chip_t = re.search(r"Chip\s+ID\s*:\s*([0-9a-fA-F]+)", b_tb, re.IGNORECASE)
        if m_chip_t:
            filtrado["toner_chip_id"] = valor_limpo(m_chip_t.group(1))
        m_pg_t = re.search(r"Bottle\s+Page\s+Count\s*[:=;]\s*(\d+)", b_tb, re.IGNORECASE)
        if m_pg_t:
            filtrado["toner_page_count"] = int(m_pg_t.group(1))
        m_lvl_t = re.search(r"Current\s+Level\s*=\s*(\d+)", b_tb, re.IGNORECASE)
        if m_lvl_t:
            filtrado["toner_life_remaining"] = int(m_lvl_t.group(1))

    # 6.2 ST Supply Table Data (osikey Black Toner)
    m_osi_t = re.search(
        r"osikey\s+(?:Black\s+)?Toner\s*,\s*serial\s*([A-Za-z0-9_-]*)\s+valid\s+\d+(.*?)(?=osikey\s+|\Z)",
        texto_limpo,
        re.IGNORECASE | re.DOTALL,
    )
    if m_osi_t:
        sn_t = valor_limpo(m_osi_t.group(1))
        b_osi_t = m_osi_t.group(2)
        if sn_t and not re.fullmatch(r"0+", sn_t):
            filtrado["toner_serial"] = sn_t
        m_pn_t = re.search(r"\bpartNumber\s+([A-Za-z0-9_-]+)", b_osi_t, re.IGNORECASE)
        if m_pn_t:
            filtrado["toner_part_number"] = valor_limpo(m_pn_t.group(1))
        m_pg_osi_t = re.search(r"\bpageCount\s+(\d+)", b_osi_t, re.IGNORECASE)
        if m_pg_osi_t and "toner_page_count" not in filtrado:
            filtrado["toner_page_count"] = int(m_pg_osi_t.group(1))
        m_rem_t = re.search(r"\bpageRemain\s+(\d+)", b_osi_t, re.IGNORECASE)
        if m_rem_t:
            filtrado["toner_pages_remaining"] = int(m_rem_t.group(1))
        m_cap_t = re.search(r"\bmaxCapacity(?:Pages)?\s+(\d+)", b_osi_t, re.IGNORECASE)
        if m_cap_t:
            filtrado["toner_max_capacity"] = int(m_cap_t.group(1))
        m_lvl_osi_t = re.search(r"\blevel\s+(\d+)", b_osi_t, re.IGNORECASE)
        if m_lvl_osi_t and "toner_life_remaining" not in filtrado:
            filtrado["toner_life_remaining"] = int(m_lvl_osi_t.group(1))

    # 6.3 Complemento via consumiveis list
    if isinstance(consumiveis, list):
        for item in consumiveis:
            if isinstance(item, dict) and item.get("tipo") == "toner":
                if item.get("numero_serie") and "toner_serial" not in filtrado:
                    filtrado["toner_serial"] = item["numero_serie"]
                if item.get("part_number") and "toner_part_number" not in filtrado:
                    filtrado["toner_part_number"] = item["part_number"]
                if item.get("page_count") is not None and "toner_page_count" not in filtrado:
                    filtrado["toner_page_count"] = item["page_count"]
                elif item.get("consumido") is not None and "toner_page_count" not in filtrado:
                    filtrado["toner_page_count"] = item["consumido"]
                if item.get("restante") is not None and "toner_pages_remaining" not in filtrado:
                    filtrado["toner_pages_remaining"] = item["restante"]
                if item.get("capacidade") is not None and "toner_max_capacity" not in filtrado:
                    filtrado["toner_max_capacity"] = item["capacidade"]
                if item.get("nivel") is not None and "toner_life_remaining" not in filtrado:
                    filtrado["toner_life_remaining"] = item["nivel"]

    return filtrado


# ============================================================
# PARSER PRINCIPAL
# ============================================================

def parse_sysdebug(texto):
    """
    Analisa o relatório SYSDEBUG tradicional.

    A MS622 utiliza o parser de Engine Debug separado.
    """

    dados = {}

    if not texto:
        return dados

    texto_limpo = limpar_html(
        texto
    )

    # ========================================================
    # FABRICANTE
    # ========================================================

    fabricante = extrair_fabricante(
        texto_limpo
    )

    if fabricante:
        dados["fabricante"] = fabricante

    # ========================================================
    # MODELO
    # ========================================================

    modelo = extrair_modelo(
        texto_limpo
    )

    if modelo:
        dados["modelo"] = modelo

    # ========================================================
    # SERIAL
    # ========================================================

    serial = extrair_serial_maquina(
        texto_limpo
    )

    if serial:
        dados["serial"] = serial

    # ========================================================
    # FIRMWARE
    # ========================================================

    firmware = extrair_firmware(
        texto_limpo
    )

    if firmware:
        dados["firmware"] = firmware

    # ========================================================
    # CONTADOR
    # ========================================================

    contador, origem = extrair_contador(
        texto_limpo
    )

    if contador is not None:

        dados["contador"] = contador
        dados["origem_contador"] = origem

    # ========================================================
    # CONSUMÍVEIS
    # ========================================================

    consumiveis = (
        extrair_consumiveis_sysdebug(
            texto
        )
    )

    if consumiveis:
        dados["consumiveis"] = consumiveis

    sysdebug_filtered = extrair_sysdebug_filtered(
        texto_limpo,
        consumiveis,
    )
    if sysdebug_filtered:
        dados["sysdebug_filtered"] = sysdebug_filtered

    return dados


# ============================================================
# CONTADOR
# ============================================================

def coletar_contador(ip):

    dados = coletar_sysdebug(
        ip
    )

    return dados.get(
        "contador"
    )


# ============================================================
# TESTE DIRETO
# ============================================================

def teste():

    print()
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - TESTE SYSDEBUG"
    )
    print("=" * 72)
    print()

    ip = input(
        "IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP não informado."
        )

        return

    print()

    dados = coletar_sysdebug(
        ip
    )

    print()
    print("=" * 72)
    print(
        "RESULTADO SYSDEBUG"
    )
    print("=" * 72)
    print()

    print(
        "Fabricante:",
        dados.get(
            "fabricante",
            "Desconhecido",
        ),
    )

    print(
        "Modelo:",
        dados.get(
            "modelo",
            "Desconhecido",
        ),
    )

    print(
        "Serial:",
        dados.get(
            "serial",
            "Desconhecido",
        ),
    )

    contador = dados.get(
        "contador"
    )

    if contador is None:

        print(
            "Contador: desconhecido"
        )

    else:

        print(
            "Contador:",
            f"{contador:,}".replace(
                ",",
                ".",
            ),
        )

    print(
        "Origem:",
        dados.get(
            "origem_contador",
            "desconhecida",
        ),
    )

    print(
        "Firmware:",
        dados.get(
            "firmware",
            "Desconhecido",
        ),
    )

    print()

    print(
        "Consumíveis SYSDEBUG:"
    )

    consumiveis = dados.get(
        "consumiveis",
        [],
    )

    if not consumiveis:

        print(
            "    Nenhum consumível reconhecido."
        )

    else:

        for numero, supply in enumerate(
            consumiveis,
            start=1,
        ):

            print()

            print(
                f"    [{numero}]",
                supply.get(
                    "nome",
                    "Consumível",
                ),
            )

            print(
                "        Tipo:",
                supply.get(
                    "tipo",
                    "",
                ),
            )

            print(
                "        Nº série:",
                supply.get(
                    "numero_serie",
                    "N/D",
                ),
            )

            part_number = supply.get(
                "part_number"
            )

            if part_number:

                print(
                    "        Part Number:",
                    part_number,
                )

    print()

    print("=" * 72)

    print(
        "TESTE CONCLUÍDO"
    )

    print("=" * 72)

    print()


if __name__ == "__main__":
    teste()