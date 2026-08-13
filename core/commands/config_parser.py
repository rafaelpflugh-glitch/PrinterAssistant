"""
Printer Assistant - PJL Config Parser

Interpreta a resposta bruta de:

@PJL INFO CONFIG

Não executa comandos.
Não conversa com a impressora.
Apenas transforma texto PJL em dados estruturados.
"""


import re


def _numero(valor):
    if valor is None:
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _lista_enumerada(texto, nome):
    """
    Extrai:

    NOME [N ENUMERATED]
    ITEM1
    ITEM2
    ...

    até o próximo campo de configuração.
    """

    padrao = rf"{re.escape(nome)}\s+\[(\d+)\s+ENUMERATED\](.*?)(?=\n[A-Z][A-Z0-9 _-]*(?:\s*=|\s+\[)|\Z)"

    encontrado = re.search(
        padrao,
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not encontrado:
        return []

    bloco = encontrado.group(2)

    itens = []

    for linha in bloco.splitlines():

        linha = linha.strip()

        if not linha:
            continue

        itens.append(linha)

    return itens


def interpretar_configuracao_pjl(texto):
    """
    Recebe a resposta de @PJL INFO CONFIG
    e retorna um dicionário estruturado.
    """

    if not texto:
        return {}

    texto = str(texto).replace(
        "\x0c",
        "",
    )

    resultado = {

        "bandejas": [],

        "saidas": [],

        "papeis": [],

        "linguagens": [],

        "ustatus": [],

        "duplex": False,

        "disco": None,

        "memoria": None,

        "display_linhas": None,

        "display_tamanho": None,

        "firmware_sistema": None,

        "firmware_scanner": None,

        "firmware_scanner_boot": None,

        "firmware_scanner_duplex": None,

        "firmware_fontes": None,

        "firmware_engine": None,

        "velocidade_engine": None,

        "serial": None,
    }


    # =====================================================
    # LISTAS
    # =====================================================

    resultado["bandejas"] = _lista_enumerada(
        texto,
        "IN TRAYS",
    )

    resultado["saidas"] = _lista_enumerada(
        texto,
        "OUTPUT BINS",
    )

    resultado["papeis"] = _lista_enumerada(
        texto,
        "PAPERS",
    )

    resultado["linguagens"] = _lista_enumerada(
        texto,
        "LANGUAGES",
    )

    resultado["ustatus"] = _lista_enumerada(
        texto,
        "USTATUS",
    )


    # =====================================================
    # DUPLEX
    # =====================================================

    resultado["duplex"] = bool(
        re.search(
            r"(?m)^\s*DUPLEX\s*$",
            texto,
            flags=re.IGNORECASE,
        )
    )


    # =====================================================
    # VALORES SIMPLES
    # =====================================================

    padroes = {

        "disco": r"(?im)^\s*DISK\s*=\s*(\d+)",

        "memoria": r"(?im)^\s*MEMORY\s*=\s*(\d+)",

        "display_linhas":
            r"(?im)^\s*DISPLAY\s+LINES\s*=\s*(\d+)",

        "display_tamanho":
            r"(?im)^\s*DISPLAY\s+CHARACTER\s+SIZE\s*=\s*(\d+)",

        "firmware_sistema":
            r"(?im)^\s*SYSTEM\s+FIRMWARE\s+VERSION\s*=\s*(.+)",

        "firmware_scanner":
            r"(?im)^\s*SCANNER\s+FIRMWARE\s+VERSION\s*=\s*(.+)",

        "firmware_scanner_boot":
            r"(?im)^\s*SCANNER\s+BOOT\s+FIRMWARE\s+VERSION\s*=\s*(.+)",

        "firmware_scanner_duplex":
            r"(?im)^\s*SCANNER\s+DUPLEX\s+FIRMWARE\s*VERSION\s*=\s*(.+)",

        "firmware_fontes":
            r"(?im)^\s*FONT\s+FIRMWARE\s+VERSION\s*=\s*(.+)",

        "firmware_engine":
            r"(?im)^\s*ENGINE\s+FIRMWARE\s+VERSION\s*=\s*(.+)",

        "velocidade_engine":
            r"(?im)^\s*ENGINE\s+SPEED\s*=\s*(\d+)",

        "serial":
            r"(?im)^\s*SERIAL\s+NUMBER\s*=\s*(.+)",
    }


    for campo, padrao in padroes.items():

        encontrado = re.search(
            padrao,
            texto,
        )

        if not encontrado:
            continue

        valor = encontrado.group(1).strip()

        if campo in (
            "disco",
            "memoria",
            "display_linhas",
            "display_tamanho",
            "velocidade_engine",
        ):

            valor = _numero(valor)

        resultado[campo] = valor


    return resultado


def formatar_bytes(valor):
    """
    Converte bytes para uma apresentação legível.
    """

    if valor is None:
        return "Desconhecido"

    try:
        valor = int(valor)
    except (TypeError, ValueError):
        return "Desconhecido"

    unidades = (
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    )

    numero = float(valor)

    for unidade in unidades:

        if numero < 1024:
            return f"{numero:.0f} {unidade}"

        numero /= 1024

    return f"{numero:.1f} PB"


def formatar_configuracao(config):
    """
    Gera apresentação limpa para o terminal.
    """

    if not config:
        return "Configuração PJL indisponível."


    linhas = []

    linhas.append("")
    linhas.append("=" * 72)
    linhas.append("CONFIGURAÇÃO DA IMPRESSORA")
    linhas.append("=" * 72)


    # =====================================================
    # PAPEL
    # =====================================================

    linhas.append("")
    linhas.append(
        f"Tipos de papel: {len(config['papeis'])}"
    )

    if config["papeis"]:

        linhas.append(
            "  " + ", ".join(
                config["papeis"]
            )
        )


    # =====================================================
    # BANDEJAS
    # =====================================================

    linhas.append("")
    linhas.append(
        f"Bandejas: {len(config['bandejas'])}"
    )

    for item in config["bandejas"]:

        linhas.append(
            f"  - {item}"
        )


    # =====================================================
    # SAÍDAS
    # =====================================================

    if config["saidas"]:

        linhas.append("")
        linhas.append(
            f"Saídas: {len(config['saidas'])}"
        )

        for item in config["saidas"]:

            linhas.append(
                f"  - {item}"
            )


    # =====================================================
    # DUPLEX
    # =====================================================

    linhas.append("")
    linhas.append(
        "Duplex:",
        if False else ""
    )

    linhas[-1] = (
        "Duplex: "
        + (
            "ATIVO"
            if config["duplex"]
            else "INATIVO"
        )
    )


    # =====================================================
    # LINGUAGENS
    # =====================================================

    linhas.append(
        "Linguagens: "
        + (
            ", ".join(
                config["linguagens"]
            )
            if config["linguagens"]
            else "Desconhecido"
        )
    )


    # =====================================================
    # MEMÓRIA / DISCO
    # =====================================================

    linhas.append("")
    linhas.append(
        "Memória: "
        + formatar_bytes(
            config["memoria"]
        )
    )

    linhas.append(
        "Disco: "
        + formatar_bytes(
            config["disco"]
        )
    )


    # =====================================================
    # FIRMWARE
    # =====================================================

    linhas.append("")
    linhas.append("FIRMWARE")

    linhas.append(
        "  Sistema: "
        + str(
            config["firmware_sistema"]
            or "Desconhecido"
        )
    )

    linhas.append(
        "  Scanner: "
        + str(
            config["firmware_scanner"]
            or "Desconhecido"
        )
    )

    linhas.append(
        "  Scanner boot: "
        + str(
            config["firmware_scanner_boot"]
            or "Desconhecido"
        )
    )

    linhas.append(
        "  Scanner duplex: "
        + str(
            config["firmware_scanner_duplex"]
            or "Desconhecido"
        )
    )

    linhas.append(
        "  Fontes: "
        + str(
            config["firmware_fontes"]
            or "Desconhecido"
        )
    )

    linhas.append(
        "  Engine: "
        + str(
            config["firmware_engine"]
            or "Desconhecido"
        )
    )


    # =====================================================
    # ENGINE
    # =====================================================

    linhas.append("")
    linhas.append(
        "Velocidade: "
        + (
            f"{config['velocidade_engine']} ppm"
            if config["velocidade_engine"]
            is not None
            else "Desconhecida"
        )
    )


    # =====================================================
    # SERIAL
    # =====================================================

    linhas.append(
        "Serial: "
        + str(
            config["serial"]
            or "Desconhecido"
        )
    )


    linhas.append("")
    linhas.append("=" * 72)

    return "\n".join(linhas)