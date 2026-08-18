"""
Printer Assistant - SYSDEBUG

Camada de coleta e interpretação do relatório SYSDEBUG.

Responsabilidades:
    - acessar /cgi-bin/sysdebugdata
    - preservar o HTML bruto
    - identificar fabricante
    - identificar modelo
    - identificar serial da máquina
    - identificar firmware
    - identificar contador
    - extrair consumíveis reconhecíveis
    - extrair seriais reais dos consumíveis

REGRAS DE CONSUMÍVEIS - LEXMARK

UNIDADE DE IMAGEM
-----------------

O serial real da unidade de imagem aparece no bloco:

    Mono Cartridge Imaging Unit ... S/N: XXXXX

Exemplo:

    Mono Cartridge Imaging Unit ... S/N: CAB193256741

TONER
-----

O serial real do toner aparece em:

    ST Supply Table Data

Exemplo:

    osikey Black Toner, serial CAS171590D5D valid 1,
    id 0: partNumber 50F0U0G

FUSOR / MAINTENANCE KIT
-----------------------

O Maintenance Kit pode aparecer no SYSDEBUG como:

    osikey Maintenance Kit, serial 000000000000 valid 1

Esse dado NÃO deve ser utilizado.

O parser:
    - não retorna serial de fusor;
    - não retorna part number de fusor;
    - não cria campo de serial para fusor;
    - não transforma 000000000000 em serial válido.

O contador oficial possui prioridade:

    Page Counter

fallback:

    Pg Cnt

IMPORTANTE:

O parser NÃO deve transformar qualquer número ou texto
encontrado no relatório em modelo, serial ou consumível.

Em especial:

    Speed: 0

não é modelo.
"""

import html
import re
from datetime import datetime
from pathlib import Path

import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TIMEOUT_SYSDEBUG = 10

SYSDEBUG_ENDPOINT = "/cgi-bin/sysdebugdata"

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

    texto = html.unescape(
        str(texto)
    )

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


def normalizar_texto(valor):
    """
    Normaliza texto para comparação.
    """

    if valor is None:
        return ""

    texto = str(
        valor
    ).strip().lower()

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

    for antigo, novo in (
        substituicoes.items()
    ):

        texto = texto.replace(
            antigo,
            novo,
        )

    return " ".join(
        texto.split()
    )


def valor_limpo(valor):
    """
    Limpa valores extraídos do relatório.
    """

    if valor is None:
        return None

    valor = html.unescape(
        str(valor)
    )

    valor = re.sub(
        r"<[^>]+>",
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

def salvar_relatorio_bruto(
    ip,
    texto,
):
    """
    Salva o SYSDEBUG bruto para diagnóstico futuro.
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

    arquivo = (
        pasta
        / (
            "sysdebug_"
            + agora.strftime("%H%M%S")
            + ".html"
        )
    )

    arquivo.write_text(
        texto,
        encoding="utf-8",
        errors="ignore",
    )

    return arquivo


# ============================================================
# COLETA
# ============================================================

def coletar_sysdebug(
    ip,
):
    """
    Acessa o relatório SYSDEBUG da impressora.
    """

    if not ip:

        print(
            "[SYSDEBUG] IP não informado."
        )

        return {}

    url = (
        f"http://{ip}"
        f"{SYSDEBUG_ENDPOINT}"
    )

    print(
        f"[SYSDEBUG] Consultando {url}"
    )

    try:

        resposta = requests.get(
            url,
            timeout=TIMEOUT_SYSDEBUG,
        )

    except requests.RequestException as erro:

        print(
            "[SYSDEBUG] Erro de comunicação:",
            erro,
        )

        return {}

    except Exception as erro:

        print(
            "[SYSDEBUG] Erro inesperado:",
            erro,
        )

        return {}

    if resposta.status_code != 200:

        print(
            "[SYSDEBUG] HTTP",
            resposta.status_code,
            "em",
            url,
        )

        return {}

    texto = resposta.text

    if not texto:

        print(
            "[SYSDEBUG] Relatório vazio."
        )

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

        print(
            arquivo
        )

    except Exception as erro:

        print(
            "[SYSDEBUG] Não foi possível salvar "
            "relatório bruto:",
            erro,
        )

    dados = parse_sysdebug(
        texto
    )

    dados[
        "ip"
    ] = ip

    dados[
        "origem"
    ] = "SYSDEBUG"

    print(
        "[SYSDEBUG] Campos encontrados:",
        ", ".join(
            dados.keys()
        )
        if dados
        else "nenhum",
    )

    return dados


# ============================================================
# EXTRAÇÃO DE CAMPO
# ============================================================

def extrair_campo(
    texto,
    padroes,
):
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

def extrair_serial_maquina(
    texto,
):
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

def extrair_contador(
    texto,
):
    """
    Page Counter possui prioridade absoluta.

    Depois:

        Pg Cnt
    """

    padroes = (
        (
            r"\bPage\s+Counter\s*(?:;|:|=)\s*"
            r"([0-9][0-9,.\s]*)"
        ),
        (
            r"\bPage\s+Counter\s+"
            r"([0-9][0-9,.\s]*)"
        ),
    )

    for padrao in padroes:

        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE,
        )

        if encontrado:

            bruto = (
                encontrado.group(1)
                .strip()
            )

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
        (
            r"\bPg\s+Cnt\s*(?:;|:|=)\s*"
            r"([0-9][0-9,.\s]*)"
        ),
        (
            r"\bPg\s+Cnt\s+"
            r"([0-9][0-9,.\s]*)"
        ),
    )

    for padrao in padroes_fallback:

        encontrado = re.search(
            padrao,
            texto,
            re.IGNORECASE,
        )

        if encontrado:

            bruto = (
                encontrado.group(1)
                .strip()
            )

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

def extrair_modelo(
    texto,
):
    """
    Extrai modelo somente de campos conhecidos.

    NÃO usa "Speed" como fallback.
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

        if normalizado.startswith(
            "speed"
        ):

            modelo = None

    if modelo:

        return modelo.strip()

    # --------------------------------------------------------
    # Fallback específico para Lexmark.
    # --------------------------------------------------------

    padrao_lexmark = (
        r"\b"
        r"(?:MX|MS|CX|CS|XM)"
        r"\s*\d{3}"
        r"(?:[A-Z]{0,3})?"
        r"\b"
    )

    encontrado = re.search(
        padrao_lexmark,
        texto,
        re.IGNORECASE,
    )

    if encontrado:

        return (
            encontrado.group(0)
            .replace(" ", "")
            .upper()
        )

    return None


# ============================================================
# FIRMWARE
# ============================================================

def extrair_firmware(
    texto,
):
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
    ).startswith(
        "speed"
    ):

        return None

    return valor


# ============================================================
# FABRICANTE
# ============================================================

def extrair_fabricante(
    texto,
):
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

def tipo_consumivel(
    nome,
):
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
# CONSUMÍVEIS DO SYSDEBUG
# ============================================================

def extrair_consumiveis_sysdebug(
    texto,
):
    """
    Extrai os consumíveis reais dos blocos conhecidos
    do SYSDEBUG.

    UNIDADE DE IMAGEM
    -----------------

    Pesquisa:

        Mono Cartridge Imaging Unit

    e extrai:

        S/N: XXXXX

    TONER
    -----

    Pesquisa:

        ST Supply Table Data

    e extrai:

        osikey Black Toner, serial XXXXX valid 1,
        id 0: partNumber XXXXX

    FUSOR / MAINTENANCE KIT
    -----------------------

    É deliberadamente ignorado.

    Mesmo que exista:

        serial 000000000000

    nenhum registro de fusor é criado.

    Isso é intencional.
    """

    consumiveis = []

    if not texto:

        return consumiveis

    texto_limpo = limpar_html(
        texto
    )

    # ========================================================
    # UNIDADE DE IMAGEM
    # ========================================================

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

        serial = valor_limpo(
            encontrado.group(1)
        )

        if serial:

            consumiveis.append(
                {
                    "tipo":
                        "unidade_imagem",

                    "nome":
                        "Mono Cartridge Imaging Unit",

                    "numero_serie":
                        serial,
                }
            )

    # ========================================================
    # TONER
    # ========================================================

    padrao_toner = re.compile(
        r"osikey\s+"
        r"([^,\r\n]+)"
        r",\s*serial\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)"
        r"\s+valid\s+1"
        r".{0,500}?"
        r"partNumber\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)",
        re.IGNORECASE | re.DOTALL,
    )

    for encontrado in padrao_toner.finditer(
        texto_limpo
    ):

        nome = valor_limpo(
            encontrado.group(1)
        )

        serial = valor_limpo(
            encontrado.group(2)
        )

        part_number = valor_limpo(
            encontrado.group(3)
        )

        if not serial:

            continue

        # ----------------------------------------------------
        # PROTEÇÃO ABSOLUTA CONTRA MAINTENANCE KIT
        # ----------------------------------------------------

        if (
            "maintenance kit"
            in normalizar_texto(
                nome
            )
        ):

            continue

        if (
            "fuser"
            in normalizar_texto(
                nome
            )
        ):

            continue

        consumiveis.append(
            {
                "tipo":
                    "toner",

                "nome":
                    nome or "Black Toner",

                "numero_serie":
                    serial,

                "part_number":
                    part_number,
            }
        )

    return consumiveis


# ============================================================
# PARSER PRINCIPAL
# ============================================================

def parse_sysdebug(
    texto,
):
    """
    Analisa o relatório SYSDEBUG.
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

        dados[
            "fabricante"
        ] = fabricante

    # ========================================================
    # MODELO
    # ========================================================

    modelo = extrair_modelo(
        texto_limpo
    )

    if modelo:

        dados[
            "modelo"
        ] = modelo

    # ========================================================
    # SERIAL DA MÁQUINA
    # ========================================================

    serial = extrair_serial_maquina(
        texto_limpo
    )

    if serial:

        dados[
            "serial"
        ] = serial

    # ========================================================
    # FIRMWARE
    # ========================================================

    firmware = extrair_firmware(
        texto_limpo
    )

    if firmware:

        dados[
            "firmware"
        ] = firmware

    # ========================================================
    # CONTADOR
    # ========================================================

    contador, origem = (
        extrair_contador(
            texto_limpo
        )
    )

    if contador is not None:

        dados[
            "contador"
        ] = contador

        dados[
            "origem_contador"
        ] = origem

    # ========================================================
    # CONSUMÍVEIS
    # ========================================================

    consumiveis = (
        extrair_consumiveis_sysdebug(
            texto
        )
    )

    if consumiveis:

        dados[
            "consumiveis"
        ] = consumiveis

    # ========================================================
    # RETORNO
    # ========================================================

    return dados


# ============================================================
# CONTADOR
# ============================================================

def coletar_contador(
    ip,
):
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