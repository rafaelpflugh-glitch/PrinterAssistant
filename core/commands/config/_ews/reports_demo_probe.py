import sys
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ============================================================
# PRINTER ASSISTANT
# MX611 - EWS DEMO / REPORTS DEEP READ-ONLY PROBE
# ============================================================
#
# OBJETIVO:
# Investigar a superfície de demonstração e relatórios da EWS
# da Lexmark MX611.
#
# REGRAS DE SEGURANÇA:
# - SOMENTE GET
# - NÃO envia POST
# - NÃO envia PUT
# - NÃO envia DELETE
# - NÃO envia formulários
# - NÃO executa links
# - NÃO imprime
# - NÃO altera configurações
# - NÃO executa RESET
# - NÃO executa DEFAULT
#
# ============================================================


TIMEOUT = 8

HEADERS = {
    "User-Agent": "PrinterAssistant-MX611-ReadOnly-Probe/1.0"
}


# ------------------------------------------------------------
# Cores ANSI
# ------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
GRAY = "\033[90m"


def banner(text):
    print()
    print("=" * 80)
    print(text)
    print("=" * 80)


def section(text):
    print()
    print("-" * 80)
    print(text)
    print("-" * 80)


def normalize_url(base, value):
    if not value:
        return None

    value = value.strip()

    if value.startswith("#"):
        return None

    return urljoin(base, value)


def same_host(url, ip):
    try:
        return urlparse(url).hostname == ip
    except Exception:
        return False


def relevant(text):
    terms = [
        "demo",
        "demonstr",
        "report",
        "relat",
        "asset",
        "inventory",
        "device",
        "configuration",
        "config",
        "statistics",
        "event",
        "profile",
        "scan",
        "printer",
        "print",
        "reset",
        "default",
        "restore",
        "factory",
    ]

    low = text.lower()

    return [term for term in terms if term in low]


def print_matches(text, terms):
    soup = BeautifulSoup(text, "html.parser")

    visible = soup.get_text(" ", strip=True)

    low = visible.lower()

    for term in terms:
        positions = []

        start = 0

        while True:
            pos = low.find(term, start)

            if pos == -1:
                break

            positions.append(pos)
            start = pos + len(term)

        if not positions:
            continue

        print()
        print(f"[{term}] {len(positions)} ocorrência(s)")

        for pos in positions[:5]:
            begin = max(0, pos - 140)
            end = min(len(visible), pos + 260)

            snippet = visible[begin:end]

            print("  ...", snippet, "...")

    return visible


def inspect_page(session, url, ip):
    print()
    print(f"{CYAN}Consultando:{RESET}")
    print(url)

    started = time.time()

    try:
        response = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )
    except Exception as exc:
        print(f"{RED}ERRO:{RESET} {exc}")
        return None

    elapsed = time.time() - started

    print()
    print("STATUS      :", response.status_code)
    print("FINAL URL   :", response.url)
    print("CONTENT     :", response.headers.get("Content-Type"))
    print("BYTES       :", len(response.content))
    print("TEMPO       :", f"{elapsed:.3f}s")

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" not in content_type:
        print(f"{YELLOW}Não é HTML. Ignorando análise estrutural.{RESET}")
        return response

    html = response.text

    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    print("TITLE       :", title)

    # --------------------------------------------------------
    # TERMOS
    # --------------------------------------------------------

    section("TERMOS RELEVANTES")

    visible = print_matches(
        html,
        [
            "demo",
            "demonstr",
            "report",
            "relat",
            "asset",
            "inventory",
            "device",
            "configuration",
            "config",
            "statistics",
            "event",
            "profile",
            "scan",
            "printer",
            "print",
            "reset",
            "default",
            "restore",
            "factory",
        ],
    )

    # --------------------------------------------------------
    # LINKS
    # --------------------------------------------------------

    section("LINKS")

    links = []

    for tag in soup.find_all("a"):
        href = tag.get("href")
        text = tag.get_text(" ", strip=True)

        full = normalize_url(response.url, href)

        if not full:
            continue

        links.append((text, full))

    unique = {}

    for text, full in links:
        unique[full] = text

    for full, text in sorted(unique.items()):
        marker = ""

        if same_host(full, ip):
            marker = "[LOCAL]"

        print(f"  {marker} {full}")

        if text:
            print(f"       texto: {text}")

    # --------------------------------------------------------
    # FORMS
    # --------------------------------------------------------

    section("FORMULÁRIOS")

    forms = soup.find_all("form")

    if not forms:
        print("Nenhum formulário encontrado.")

    for index, form in enumerate(forms, 1):

        method = form.get("method", "GET").upper()
        action = normalize_url(response.url, form.get("action", ""))

        print()
        print(f"FORM {index}")
        print("  method :", method)
        print("  action :", action)

        for field in form.find_all(
            ["input", "select", "textarea", "button"]
        ):

            print(
                "  campo  :",
                "tag=", field.name,
                "name=", field.get("name"),
                "type=", field.get("type"),
                "value=", field.get("value"),
            )

    # --------------------------------------------------------
    # JAVASCRIPT
    # --------------------------------------------------------

    section("JAVASCRIPT / MECANISMOS")

    scripts = soup.find_all("script")

    print("Scripts encontrados:", len(scripts))

    interesting_js = [
        "window.location",
        "location.href",
        "location.replace",
        "location.assign",
        "document.location",
        "form.submit",
        "submit(",
        "XMLHttpRequest",
        "fetch(",
        "cgi-bin",
        "postpf",
        "report",
        "asset",
        "demo",
        "scan",
        "profile",
        "reset",
        "default",
        "factory",
    ]

    for index, script in enumerate(scripts, 1):

        src = script.get("src")

        if src:
            full_src = normalize_url(response.url, src)

            print()
            print(f"SCRIPT {index}")
            print("  SRC:", full_src)

            # IMPORTANTE:
            # O probe não baixa/executa JS externo.
            continue

        js = script.get_text("\n", strip=True)

        if not js:
            continue

        low = js.lower()

        found = []

        for term in interesting_js:
            if term.lower() in low:
                found.append(term)

        if not found:
            continue

        print()
        print(f"SCRIPT INLINE {index}")
        print("  termos:", ", ".join(found))

        for term in found:
            pos = low.find(term.lower())

            begin = max(0, pos - 180)
            end = min(len(js), pos + 420)

            print()
            print(f"  [{term}]")
            print("  ", js[begin:end].replace("\n", " "))

    # --------------------------------------------------------
    # BOTÕES
    # --------------------------------------------------------

    section("BOTÕES")

    buttons = soup.find_all("button")

    if not buttons:
        print("Nenhum <button> encontrado.")

    for index, button in enumerate(buttons, 1):

        print(
            f"BUTTON {index}:",
            "text=", button.get_text(" ", strip=True),
            "type=", button.get("type"),
            "name=", button.get("name"),
            "value=", button.get("value"),
            "onclick=", button.get("onclick"),
        )

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    section("INPUTS")

    inputs = soup.find_all("input")

    if not inputs:
        print("Nenhum input encontrado.")

    for index, field in enumerate(inputs, 1):

        print(
            f"INPUT {index}:",
            "type=", field.get("type"),
            "name=", field.get("name"),
            "value=", field.get("value"),
            "onclick=", field.get("onclick"),
        )

    return response


def main():

    banner(
        "PRINTER ASSISTANT - MX611 EWS DEMO / REPORTS DEEP PROBE"
    )

    print()
    print("OBJETIVO:")
    print("Investigar DEMO / REPORTS / ASSET / SCANNER.")
    print()
    print("MODO:")
    print("SOMENTE LEITURA")
    print()
    print("PROIBIDO:")
    print("  POST")
    print("  PUT")
    print("  DELETE")
    print("  RESET")
    print("  DEFAULT")
    print("  PRINT")
    print("  SUBMIT")
    print("  EXECUÇÃO DE LINKS")
    print("  EXECUÇÃO DE JAVASCRIPT")

    print()

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
        sys.exit(1)

    print()
    print("Impressora:", ip)

    confirm = input("\nContinuar? [S/N]: ").strip().upper()

    if confirm != "S":
        print("Cancelado.")
        return

    session = requests.Session()

    session.headers.update(HEADERS)

    # --------------------------------------------------------
    # CANDIDATOS PRINCIPAIS
    # --------------------------------------------------------

    paths = [
        "/",
        "/cgi-bin/dynamic/",
        "/cgi-bin/dynamic/reports_and_information.html",
        "/cgi-bin/dynamic/config/config.html",
        "/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
        "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",
        "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",
        "/cgi-bin/dynamic/printer/config/reports/eventlog.html",
        "/cgi-bin/dynamic/printer/config/reports/printprofile.html",
        "/cgi-bin/dynamic/printer/config/reports/shortcutreport.html",
        "/cgi-bin/dynamic/printer/config/gen/scan2net.html",
        "/cgi-bin/dynamic/printer/config/scanprofile/createprofile.html",
        "/cgi-bin/dynamic/printer/config/gen/setuppg.html",
        "/cgi-bin/dynamic/printer/config/gen/printersettings.html",
        "/cgi-bin/dynamic/printer/config/gen/general.html",
    ]

    results = []

    # --------------------------------------------------------
    # HTTP
    # --------------------------------------------------------

    banner("SUPERFÍCIE HTTP")

    for path in paths:

        url = f"http://{ip}{path}"

        response = inspect_page(
            session,
            url,
            ip,
        )

        if response is not None:
            results.append(response)

    # --------------------------------------------------------
    # HTTPS
    # --------------------------------------------------------

    banner("SUPERFÍCIE HTTPS")

    for path in paths:

        url = f"https://{ip}{path}"

        response = inspect_page(
            session,
            url,
            ip,
        )

        if response is not None:
            results.append(response)

    # --------------------------------------------------------
    # RESUMO
    # --------------------------------------------------------

    banner("RESULTADO DO DEEP PROBE")

    successful = [
        r for r in results
        if r is not None and r.status_code == 200
    ]

    print("Páginas testadas :", len(results))
    print("HTTP 200         :", len(successful))

    print()
    print("IMPORTANTE:")
    print("Este teste NÃO executou nenhum mecanismo.")
    print("Nenhum formulário foi submetido.")
    print("Nenhum POST foi enviado.")
    print("Nenhum SET foi enviado.")
    print("Nenhum RESET foi enviado.")
    print("Nenhum DEFAULT foi enviado.")
    print("Nenhum PRINT foi solicitado.")

    banner("FIM DO DEEP PROBE")


if __name__ == "__main__":
    main()