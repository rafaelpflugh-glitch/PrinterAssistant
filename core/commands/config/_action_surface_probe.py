"""
PRINTER ASSISTANT
MX611 ACTION SURFACE PROBE

Objetivo:

Mapear as superfícies disponíveis para ações reais
na Lexmark MX611dhe antes de começar a implementar
comandos de alteração.

Este probe NÃO altera configurações.

Ele investiga:

    1. PJL INFO ID
    2. PJL INFO STATUS
    3. PJL INFO VARIABLES
    4. PJL INFO CONFIG
    5. PJL INFO USTATUS
    6. PJL INQUIRE de variáveis relevantes
    7. PJL DINQUIRE das mesmas variáveis
    8. Interface HTTP/EWS
    9. páginas e links encontrados no EWS
   10. referências aparentes a:
          - language
          - firmware
          - settings
          - home
          - buttons
          - display
          - configuration
          - administrator

IMPORTANTE:

Este arquivo NÃO executa:

    @PJL SET
    @PJL DEFAULT
    @PJL RESET
    @PJL INITIALIZE

Também não envia job.

Também não imprime.

Também não executa atualização de firmware.

A finalidade é descobrir onde as futuras ações
devem ser implementadas.
"""

from __future__ import annotations

import re
import socket
import time
import urllib.error
import urllib.request
from html import unescape


# ============================================================
# CONFIGURAÇÃO
# ============================================================

RAW_PORT = 9100

HTTP_PORTS = [
    80,
    443,
]

HTTP_TIMEOUT = 5
RAW_TIMEOUT = 5


# ============================================================
# VARIÁVEIS PJL RELEVANTES
# ============================================================

PJL_VARIABLES = [
    "LANG",
    "LANGUAGE",
    "PAPER",
    "MEDIATYPE",
    "DUPLEX",
    "COPIES",
    "RESOLUTION",
    "DENSITY",
    "ORIENTATION",
    "ECONOMODE",
    "TIMEZONE",
    "COUNTRY",
    "COUNTRYCODE",
    "OUTPUTBIN",
    "MEDIASOURCE",
    "TRAY",
    "INPUTTRAY",
    "MEDIAWEIGHT",
    "MEDIATEXTURE",
]


# ============================================================
# PALAVRAS IMPORTANTES PARA EWS
# ============================================================

INTERESTING_TERMS = [
    "language",
    "lang",
    "firmware",
    "settings",
    "setting",
    "configuration",
    "config",
    "home",
    "button",
    "buttons",
    "display",
    "screen",
    "panel",
    "administrator",
    "admin",
    "update",
    "upgrade",
    "system",
    "device",
]


# ============================================================
# RAW PJL
# ============================================================


def raw_command(
    ip: str,
    command: str,
    timeout: int = RAW_TIMEOUT,
) -> str:
    """
    Envia somente comandos de consulta PJL.

    O comando é encerrado com CRLF.

    Não executa comandos de alteração.
    """

    sock = None

    try:
        print(
            f"Conectando em {ip}:{RAW_PORT}..."
        )

        sock = socket.create_connection(
            (ip, RAW_PORT),
            timeout=timeout,
        )

        sock.settimeout(timeout)

        if not command.endswith("\r\n"):
            command += "\r\n"

        print(
            f"  >> {command.strip()}"
        )

        inicio = time.perf_counter()

        sock.sendall(
            command.encode(
                "ascii",
                errors="replace",
            )
        )

        resposta = bytearray()

        while True:

            try:

                bloco = sock.recv(8192)

                if not bloco:
                    break

                resposta.extend(bloco)

                if len(bloco) < 8192:
                    break

            except socket.timeout:
                break

        tempo = (
            time.perf_counter()
            - inicio
        )

        texto = resposta.decode(
            "latin-1",
            errors="replace",
        )

        print(
            f"  << {len(resposta)} bytes "
            f"em {tempo:.3f}s"
        )

        return texto

    except Exception as exc:

        print(
            f"  !! ERRO: "
            f"{type(exc).__name__}: {exc}"
        )

        return ""

    finally:

        if sock is not None:

            try:
                sock.close()
            except OSError:
                pass


# ============================================================
# EXIBIÇÃO PJL
# ============================================================


def print_response(
    title: str,
    response: str,
) -> None:

    print()
    print("-" * 72)
    print(title)
    print("-" * 72)

    if not response:

        print(
            "(sem resposta)"
        )

        return

    print(response.rstrip())


# ============================================================
# HTTP
# ============================================================


def http_request(
    ip: str,
    port: int,
) -> tuple[str, str]:

    if port == 443:
        scheme = "https"
    else:
        scheme = "http"

    url = (
        f"{scheme}://{ip}/"
    )

    print()
    print(
        f"HTTP: {url}"
    )

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "PrinterAssistant/"
                    "MX611-ActionSurfaceProbe",
            },
        )

        inicio = time.perf_counter()

        with urllib.request.urlopen(
            request,
            timeout=HTTP_TIMEOUT,
        ) as response:

            data = response.read()

            tempo = (
                time.perf_counter()
                - inicio
            )

            charset = (
                response.headers.get_content_charset()
                or "latin-1"
            )

            texto = data.decode(
                charset,
                errors="replace",
            )

            print(
                f"  Status : "
                f"{response.status}"
            )

            print(
                f"  Bytes  : "
                f"{len(data)}"
            )

            print(
                f"  Tempo  : "
                f"{tempo:.3f}s"
            )

            print(
                f"  Tipo   : "
                f"{response.headers.get('Content-Type')}"
            )

            return url, texto

    except urllib.error.HTTPError as exc:

        print(
            f"  HTTP ERROR "
            f"{exc.code}: {exc.reason}"
        )

        return url, ""

    except urllib.error.URLError as exc:

        print(
            f"  URL ERROR: "
            f"{exc.reason}"
        )

        return url, ""

    except Exception as exc:

        print(
            f"  ERRO: "
            f"{type(exc).__name__}: {exc}"
        )

        return url, ""


# ============================================================
# EXTRAÇÃO DE LINKS
# ============================================================


def extract_links(
    base_url: str,
    html: str,
) -> list[str]:

    links = []

    pattern = re.compile(
        r"""href\s*=\s*["']([^"']+)["']""",
        re.IGNORECASE,
    )

    for match in pattern.finditer(html):

        href = unescape(
            match.group(1).strip()
        )

        if not href:
            continue

        if href.startswith("#"):
            continue

        links.append(href)

    # Remove duplicados preservando ordem.

    resultado = []

    vistos = set()

    for link in links:

        if link in vistos:
            continue

        vistos.add(link)

        resultado.append(link)

    return resultado


# ============================================================
# EXTRAÇÃO DE TERMOS
# ============================================================


def find_interesting_terms(
    html: str,
) -> dict[str, list[str]]:

    resultado = {}

    texto = html.lower()

    for term in INTERESTING_TERMS:

        posicoes = []

        inicio = 0

        while True:

            pos = texto.find(
                term,
                inicio,
            )

            if pos == -1:
                break

            posicoes.append(pos)

            inicio = pos + len(term)

            if len(posicoes) >= 10:
                break

        if posicoes:
            resultado[term] = posicoes

    return resultado


# ============================================================
# CONTEXTO DOS TERMOS
# ============================================================


def print_term_context(
    html: str,
    matches: dict[str, list[str]],
) -> None:

    if not matches:
        print()
        print(
            "Nenhum termo relevante "
            "encontrado."
        )
        return

    print()
    print(
        "TERMOS RELEVANTES ENCONTRADOS"
    )
    print("-" * 72)

    texto = re.sub(
        r"\s+",
        " ",
        html,
    )

    for term, positions in matches.items():

        print()
        print(
            f"[{term}] "
            f"{len(positions)} ocorrência(s)"
        )

        exibidos = 0

        lower = texto.lower()

        for pos in positions:

            # Recalcular aproximadamente
            # porque o HTML foi normalizado.

            inicio = max(
                0,
                pos - 100,
            )

            fim = min(
                len(texto),
                pos + 200,
            )

            trecho = texto[
                inicio:fim
            ]

            print(
                f"  ...{trecho}..."
            )

            exibidos += 1

            if exibidos >= 3:
                break


# ============================================================
# PORTAS HTTP
# ============================================================


def check_port(
    ip: str,
    port: int,
) -> bool:

    print()
    print(
        f"Testando TCP "
        f"{ip}:{port}..."
    )

    try:

        with socket.create_connection(
            (ip, port),
            timeout=3,
        ):

            print(
                "  [OK] Porta aberta."
            )

            return True

    except Exception as exc:

        print(
            f"  [X] Não acessível: "
            f"{type(exc).__name__}"
        )

        return False


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    print("=" * 72)
    print(
        "PRINTER ASSISTANT - "
        "MX611 ACTION SURFACE PROBE"
    )
    print("=" * 72)

    print()
    print(
        "OBJETIVO:"
    )

    print(
        "Mapear onde as futuras ações "
        "da MX611 podem ser executadas."
    )

    print()
    print(
        "ESTE TESTE É SOMENTE DE CONSULTA."
    )

    print(
        "Nenhum SET será enviado."
    )

    print(
        "Nenhum DEFAULT será enviado."
    )

    print(
        "Nenhum RESET será enviado."
    )

    print(
        "Nenhum job será enviado."
    )

    print(
        "Nenhuma página será impressa."
    )

    print(
        "Nenhum firmware será alterado."
    )

    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP inválido."
        )

        return

    print()
    print(
        f"Impressora: {ip}"
    )

    print(
        f"RAW:        {RAW_PORT}"
    )

    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":

        print(
            "Teste cancelado."
        )

        return

    # ========================================================
    # 1. PJL ID
    # ========================================================

    print()
    print("=" * 72)
    print("1. PJL INFO ID")
    print("=" * 72)

    response_id = raw_command(
        ip,
        "@PJL INFO ID",
    )

    print_response(
        "RESPOSTA INFO ID",
        response_id,
    )

    # ========================================================
    # 2. STATUS
    # ========================================================

    print()
    print("=" * 72)
    print("2. PJL INFO STATUS")
    print("=" * 72)

    response_status = raw_command(
        ip,
        "@PJL INFO STATUS",
    )

    print_response(
        "RESPOSTA INFO STATUS",
        response_status,
    )

    # ========================================================
    # 3. VARIABLES
    # ========================================================

    print()
    print("=" * 72)
    print("3. PJL INFO VARIABLES")
    print("=" * 72)

    response_variables = raw_command(
        ip,
        "@PJL INFO VARIABLES",
    )

    print_response(
        "RESPOSTA INFO VARIABLES",
        response_variables,
    )

    # ========================================================
    # 4. CONFIG
    # ========================================================

    print()
    print("=" * 72)
    print("4. PJL INFO CONFIG")
    print("=" * 72)

    response_config = raw_command(
        ip,
        "@PJL INFO CONFIG",
    )

    print_response(
        "RESPOSTA INFO CONFIG",
        response_config,
    )

    # ========================================================
    # 5. USTATUS
    # ========================================================

    print()
    print("=" * 72)
    print("5. PJL INFO USTATUS")
    print("=" * 72)

    response_ustatus = raw_command(
        ip,
        "@PJL INFO USTATUS",
    )

    print_response(
        "RESPOSTA INFO USTATUS",
        response_ustatus,
    )

    # ========================================================
    # 6. INQUIRE / DINQUIRE
    # ========================================================

    print()
    print("=" * 72)
    print("6. MAPA DE VARIÁVEIS")
    print("=" * 72)

    print()
    print(
        "As consultas abaixo NÃO alteram "
        "a impressora."
    )

    resultados = {}

    for variable in PJL_VARIABLES:

        print()
        print(
            f"[{variable}]"
        )

        inquire = raw_command(
            ip,
            f"@PJL INQUIRE {variable}",
        )

        dinquire = raw_command(
            ip,
            f"@PJL DINQUIRE {variable}",
        )

        resultados[variable] = {
            "inquire": inquire,
            "dinquire": dinquire,
        }

        print(
            "  INQUIRE:"
        )

        if inquire:
            print(
                inquire.rstrip()
            )
        else:
            print(
                "  (sem resposta)"
            )

        print(
            "  DINQUIRE:"
        )

        if dinquire:
            print(
                dinquire.rstrip()
            )
        else:
            print(
                "  (sem resposta)"
            )

    # ========================================================
    # 7. HTTP
    # ========================================================

    print()
    print("=" * 72)
    print("7. SUPERFÍCIE HTTP / EWS")
    print("=" * 72)

    http_results = []

    for port in HTTP_PORTS:

        if not check_port(
            ip,
            port,
        ):
            continue

        url, html = http_request(
            ip,
            port,
        )

        if not html:
            continue

        http_results.append(
            (
                url,
                html,
            )
        )

        print()
        print(
            f"Página inicial: {url}"
        )

        print(
            f"Tamanho HTML: "
            f"{len(html)} bytes"
        )

        # ----------------------------------------------------
        # LINKS
        # ----------------------------------------------------

        links = extract_links(
            url,
            html,
        )

        print()
        print(
            f"LINKS ENCONTRADOS: "
            f"{len(links)}"
        )

        for link in links[:100]:

            print(
                f"  {link}"
            )

        # ----------------------------------------------------
        # TERMOS
        # ----------------------------------------------------

        matches = find_interesting_terms(
            html,
        )

        print_term_context(
            html,
            matches,
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    print()
    print("=" * 72)
    print("RESULTADO DO MAPEAMENTO")
    print("=" * 72)

    print()
    print(
        "PJL:"
    )

    print(
        "  [OK] INFO ID consultado."
    )

    print(
        "  [OK] INFO STATUS consultado."
    )

    print(
        "  [OK] INFO VARIABLES consultado."
    )

    print(
        "  [OK] INFO CONFIG consultado."
    )

    print(
        "  [OK] INFO USTATUS consultado."
    )

    print(
        "  [OK] INQUIRE/DINQUIRE consultados."
    )

    print()
    print(
        "HTTP/EWS:"
    )

    if http_results:

        print(
            "  [OK] Superfície HTTP encontrada."
        )

        for url, html in http_results:

            print(
                f"  [OK] {url} "
                f"({len(html)} bytes)"
            )

    else:

        print(
            "  [?] Nenhuma página HTTP "
            "foi obtida."
        )

    print()
    print("=" * 72)
    print("PRÓXIMA ETAPA")
    print("=" * 72)

    print()
    print(
        "Os resultados deste probe serão usados "
        "para separar as futuras ações em:"
    )

    print()
    print(
        "  1. AÇÕES PJL"
    )

    print(
        "     SET / RESET / DEFAULT / JOB"
    )

    print()
    print(
        "  2. AÇÕES EWS"
    )

    print(
        "     configurações da interface, "
        "idioma, tela inicial, botões etc."
    )

    print()
    print(
        "  3. AÇÕES DE SISTEMA"
    )

    print(
        "     firmware e operações administrativas."
    )

    print()
    print(
        "Nenhuma dessas ações será implementada "
        "como suportada até termos evidência "
        "do mecanismo correto."
    )

    print()
    print(
        "=" * 72
    )

    print(
        "FIM DO PROBE"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()