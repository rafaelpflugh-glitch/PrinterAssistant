"""
PRINTER ASSISTANT
MX611 EWS - REPORTS / SCANNER / CONFIG PROBE

Este módulo é SOMENTE DE CONSULTA.

Não executa:
- POST
- PUT
- DELETE
- SET
- RESET
- DEFAULT
- PRINT

Objetivo:
Mapear as páginas EWS relevantes descobertas no left_bar.html
da Lexmark MX611dhe e identificar:

- Asset Report
- Reports
- Scanner
- Scan Profile
- Scan to Network
- Administration / Configuration
- Reset
- Defaults
- formulários
- ações
- parâmetros
- links relacionados

Nenhuma ação encontrada é executada automaticamente.
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from html import unescape
from typing import List
from urllib.parse import urljoin, urlparse

import requests


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

MODEL = "MX611dhe"
MANUFACTURER = "Lexmark"

DEFAULT_TIMEOUT = 8

RELEVANT_TERMS = [
    "asset",
    "asset report",
    "relatório",
    "relatórios",
    "report",
    "reports",
    "scanner",
    "scan",
    "digitaliza",
    "digitalização",
    "scanprofile",
    "scan to network",
    "network",
    "reset",
    "default",
    "defaults",
    "restaur",
    "factory",
    "config",
    "administration",
    "administração",
    "apply",
    "submit",
    "save",
    "salvar",
    "print",
    "imprimir",
]


# URLs descobertas diretamente no mapa EWS anterior.
TARGET_PATHS = [
    "/cgi-bin/dynamic/reports_and_information.html",
    "/cgi-bin/dynamic/config/config.html",
    "/cgi-bin/dynamic/printer/config/scanprofile/createprofile.html",
    "/cgi-bin/dynamic/printer/config/gen/copy_printer_settings.html",
    "/cgi-bin/dynamic/printer/config/remote_oppanel.html",
]


# ============================================================================
# ESTRUTURAS
# ============================================================================

@dataclass
class PageResult:
    url: str
    status: int | None
    content_type: str
    size: int
    elapsed: float
    text: str
    final_url: str


@dataclass
class FormInfo:
    method: str
    action: str
    raw: str


# ============================================================================
# UTILIDADES
# ============================================================================

def separator(char="-", size=80):
    print(char * size)


def clean_text(value: str) -> str:
    value = unescape(value)
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_url(base_url: str, target: str) -> str:
    return urljoin(base_url, target)


def short_url(url: str, max_len: int = 140) -> str:
    if len(url) <= max_len:
        return url
    return url[: max_len - 3] + "..."


# ============================================================================
# EXTRAÇÃO
# ============================================================================

def extract_links(html: str, base_url: str) -> List[str]:
    found = []

    for match in re.finditer(
        r"""<a\b[^>]*?\bhref\s*=\s*["']([^"']+)["']""",
        html,
        flags=re.I | re.S,
    ):
        target = unescape(match.group(1).strip())

        if not target:
            continue

        if target.startswith("#"):
            continue

        url = normalize_url(base_url, target)

        if url not in found:
            found.append(url)

    return found


def extract_forms(html: str, base_url: str) -> List[FormInfo]:
    forms = []

    pattern = re.compile(
        r"<form\b([^>]*)>(.*?)</form>",
        flags=re.I | re.S,
    )

    for match in pattern.finditer(html):
        attributes = match.group(1)
        body = match.group(2)

        method_match = re.search(
            r"""\bmethod\s*=\s*["']([^"']+)["']""",
            attributes,
            flags=re.I,
        )

        action_match = re.search(
            r"""\baction\s*=\s*["']([^"']*)["']""",
            attributes,
            flags=re.I,
        )

        method = (
            method_match.group(1).upper()
            if method_match
            else "GET"
        )

        action_raw = (
            action_match.group(1)
            if action_match
            else ""
        )

        action = normalize_url(base_url, action_raw)

        forms.append(
            FormInfo(
                method=method,
                action=action,
                raw=body,
            )
        )

    return forms


def extract_inputs(form_html: str) -> List[str]:
    results = []

    for match in re.finditer(
        r"<input\b([^>]*)>",
        form_html,
        flags=re.I | re.S,
    ):
        attrs = match.group(1)

        name = re.search(
            r"""\bname\s*=\s*["']([^"']+)["']""",
            attrs,
            flags=re.I,
        )

        input_type = re.search(
            r"""\btype\s*=\s*["']([^"']+)["']""",
            attrs,
            flags=re.I,
        )

        value = re.search(
            r"""\bvalue\s*=\s*["']([^"']*)["']""",
            attrs,
            flags=re.I,
        )

        name_text = name.group(1) if name else "(sem name)"
        type_text = input_type.group(1) if input_type else "text"
        value_text = value.group(1) if value else ""

        results.append(
            f"name={name_text!r} "
            f"type={type_text!r} "
            f"value={value_text!r}"
        )

    return results


def find_relevant_terms(text: str):
    lower = text.lower()
    matches = []

    for term in RELEVANT_TERMS:
        count = lower.count(term.lower())

        if count:
            matches.append((term, count))

    return matches


def extract_context(text: str, term: str, radius: int = 180):
    lower = text.lower()
    term_lower = term.lower()

    contexts = []

    start = 0

    while True:
        index = lower.find(term_lower, start)

        if index == -1:
            break

        left = max(0, index - radius)
        right = min(len(text), index + len(term) + radius)

        fragment = text[left:right]
        fragment = re.sub(r"\s+", " ", fragment).strip()

        contexts.append(fragment)

        start = index + len(term_lower)

        if len(contexts) >= 3:
            break

    return contexts


# ============================================================================
# CONSULTA HTTP
# ============================================================================

def fetch(session: requests.Session, url: str) -> PageResult:
    started = time.perf_counter()

    try:
        response = session.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            verify=False,
            allow_redirects=True,
        )

        elapsed = time.perf_counter() - started

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        encoding = response.encoding or "utf-8"

        try:
            text = response.content.decode(
                encoding,
                errors="replace",
            )
        except Exception:
            text = response.text

        return PageResult(
            url=url,
            status=response.status_code,
            content_type=content_type,
            size=len(response.content),
            elapsed=elapsed,
            text=text,
            final_url=response.url,
        )

    except requests.RequestException as exc:
        elapsed = time.perf_counter() - started

        print()
        print(f"✗ ERRO HTTP")
        print(f"  URL    : {url}")
        print(f"  Erro   : {exc}")
        print(f"  Tempo  : {elapsed:.3f}s")

        return PageResult(
            url=url,
            status=None,
            content_type="",
            size=0,
            elapsed=elapsed,
            text="",
            final_url=url,
        )


# ============================================================================
# ANÁLISE
# ============================================================================

def analyze_page(result: PageResult):
    print()
    print("=" * 80)
    print("PÁGINA")
    print("=" * 80)

    print(f"URL        : {result.url}")
    print(f"FINAL URL  : {result.final_url}")
    print(f"STATUS     : {result.status}")
    print(f"CONTENT    : {result.content_type}")
    print(f"BYTES      : {result.size}")
    print(f"TEMPO      : {result.elapsed:.3f}s")

    if not result.text:
        print()
        print("Nenhum conteúdo recebido.")
        return [], []

    text = clean_text(result.text)

    # ------------------------------------------------------------------------
    # TERMOS
    # ------------------------------------------------------------------------

    print()
    print("TERMOS RELEVANTES")
    separator()

    terms = find_relevant_terms(text)

    if not terms:
        print("Nenhum termo relevante encontrado.")
    else:
        for term, count in terms:
            print(f"[{term}] {count} ocorrência(s)")

            contexts = extract_context(text, term)

            for context in contexts:
                print(f"  ...{context}...")

    # ------------------------------------------------------------------------
    # LINKS
    # ------------------------------------------------------------------------

    links = extract_links(
        result.text,
        result.final_url,
    )

    print()
    print("LINKS / RECURSOS")
    separator()

    if not links:
        print("Nenhum link encontrado.")
    else:
        for link in links:
            print(f"  {link}")

    # ------------------------------------------------------------------------
    # FORMS
    # ------------------------------------------------------------------------

    forms = extract_forms(
        result.text,
        result.final_url,
    )

    print()
    print("FORMULÁRIOS")
    separator()

    if not forms:
        print("Nenhum formulário encontrado.")
    else:
        for index, form in enumerate(forms, start=1):
            print(f"FORM {index}")
            print(f"  method : {form.method}")
            print(f"  action : {form.action}")

            inputs = extract_inputs(form.raw)

            if inputs:
                print("  CAMPOS:")

                for item in inputs:
                    print(f"    {item}")
            else:
                print("  CAMPOS: nenhum input encontrado")

    return links, forms


# ============================================================================
# CLASSIFICAÇÃO DE SUPERFÍCIE
# ============================================================================

def classify_url(url: str) -> str:
    lower = url.lower()

    if "reports_and_information" in lower:
        return "REPORTS / ASSET REPORT"

    if "scanprofile" in lower:
        return "SCANNER / SCAN PROFILE"

    if "scan" in lower:
        return "SCANNER / SCAN"

    if "config" in lower:
        return "CONFIGURATION"

    if "remote_oppanel" in lower:
        return "REMOTE OPERATOR PANEL"

    if "copy_printer_settings" in lower:
        return "PRINTER CONFIG COPY"

    if "reset" in lower:
        return "RESET"

    if "default" in lower:
        return "DEFAULTS"

    return "OTHER"


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("PRINTER ASSISTANT - MX611 EWS REPORTS / SCANNER PROBE")
    print("=" * 80)

    print()
    print("OBJETIVO:")
    print("Mapear as superfícies EWS relevantes descobertas na MX611.")

    print()
    print("ÁREAS INVESTIGADAS:")
    print("  1. Reports / Asset Report")
    print("  2. Scanner / Scan Profile")
    print("  3. Scan to Network")
    print("  4. Configuration")
    print("  5. Printer Defaults / Reset")
    print("  6. Remote Operator Panel")

    print()
    print("ESTE TESTE É SOMENTE DE CONSULTA.")
    print("Nenhum SET será enviado.")
    print("Nenhum RESET será enviado.")
    print("Nenhum DEFAULT será enviado.")
    print("Nenhum PRINT será solicitado.")
    print("Nenhum POST será enviado.")
    print("Nenhum formulário será submetido.")
    print("Nenhum link será executado como operação.")

    print()

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print()
        print("✗ IP não informado.")
        return 1

    # Validação simples para evitar URLs arbitrárias.
    if "/" in ip or "\\" in ip or " " in ip:
        print()
        print("✗ IP inválido.")
        return 1

    print()
    print(f"Impressora: {ip}")

    print()
    continuar = input("Continuar? [S/N]: ").strip().upper()

    if continuar != "S":
        print()
        print("Operação cancelada pelo usuário.")
        return 0

    print()
    print("=" * 80)
    print("INICIALIZAÇÃO")
    print("=" * 80)

    requests.packages.urllib3.disable_warnings()

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": "PrinterAssistant-MX611-EWS-Probe/1.0",
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    all_pages = []
    discovered_links = set()
    forms_found = []

    # ------------------------------------------------------------------------
    # HTTP E HTTPS
    # ------------------------------------------------------------------------

    for scheme in ("http", "https"):

        print()
        print("=" * 80)
        print(f"SUPERFÍCIE {scheme.upper()}")
        print("=" * 80)

        base = f"{scheme}://{ip}/"

        for path in TARGET_PATHS:

            url = urljoin(base, path)

            print()
            print(f"Consultando {url}")

            result = fetch(
                session,
                url,
            )

            all_pages.append(result)

            links, forms = analyze_page(result)

            for link in links:
                discovered_links.add(link)

            if forms:
                forms_found.append(
                    (
                        result.url,
                        forms,
                    )
                )

    # =========================================================================
    # MAPA FINAL
    # =========================================================================

    print()
    print("=" * 80)
    print("MAPA EWS - REPORTS / SCANNER / CONFIGURATION")
    print("=" * 80)

    print()
    print("PÁGINAS CONSULTADAS")
    separator()

    successful = 0

    for result in all_pages:

        status = (
            str(result.status)
            if result.status is not None
            else "ERR"
        )

        print(
            f"[{status}] "
            f"{result.url}"
        )

        if result.status == 200:
            successful += 1

    # ------------------------------------------------------------------------
    # CLASSIFICAÇÃO DOS LINKS
    # ------------------------------------------------------------------------

    print()
    print("=" * 80)
    print("SUPERFÍCIES DESCOBERTAS")
    print("=" * 80)

    classified = {}

    for link in sorted(discovered_links):

        category = classify_url(link)

        classified.setdefault(
            category,
            [],
        ).append(link)

    for category in sorted(classified):

        print()
        print(f"[{category}]")
        separator("-")

        for link in classified[category]:
            print(f"  {link}")

    # ------------------------------------------------------------------------
    # FORMULÁRIOS
    # ------------------------------------------------------------------------

    print()
    print("=" * 80)
    print("FORMULÁRIOS DESCOBERTOS")
    print("=" * 80)

    if not forms_found:

        print()
        print("Nenhum formulário encontrado.")

    else:

        counter = 0

        for page_url, forms in forms_found:

            for form in forms:

                counter += 1

                print()
                print(f"FORM {counter}")

                print(f"  página : {page_url}")
                print(f"  method : {form.method}")
                print(f"  action : {form.action}")

                inputs = extract_inputs(form.raw)

                if inputs:

                    print("  campos:")

                    for item in inputs:
                        print(f"    {item}")

                else:

                    print("  campos: nenhum")

    # ------------------------------------------------------------------------
    # CANDIDATOS
    # ------------------------------------------------------------------------

    print()
    print("=" * 80)
    print("CANDIDATOS PARA INVESTIGAÇÃO")
    print("=" * 80)

    candidates = []

    for link in sorted(discovered_links):

        lower = link.lower()

        if any(
            term in lower
            for term in (
                "report",
                "reports",
                "asset",
                "scan",
                "scanner",
                "reset",
                "default",
                "config",
            )
        ):
            candidates.append(link)

    if not candidates:

        print()
        print("Nenhum candidato adicional encontrado.")

    else:

        for candidate in candidates:

            print()
            print(f"[CANDIDATO]")
            print(f"  superfície : {classify_url(candidate)}")
            print(f"  URL        : {candidate}")

    # =========================================================================
    # RESULTADO
    # =========================================================================

    print()
    print("=" * 80)
    print("RESULTADO DO PROBE")
    print("=" * 80)

    print()
    print(f"Páginas consultadas : {len(all_pages)}")
    print(f"Páginas respondendo : {successful}")
    print(f"Links descobertos   : {len(discovered_links)}")
    print(f"Formulários         : {sum(len(f) for _, f in forms_found)}")
    print(f"Candidatos          : {len(candidates)}")

    print()
    print("IMPORTANTE:")
    print("Este probe NÃO considera nenhum mecanismo como suportado.")
    print("Nenhum formulário foi submetido.")
    print("Nenhuma operação foi executada.")
    print("Nenhum mecanismo foi promovido para EXEC.")

    print()
    print("PRÓXIMA ETAPA:")
    print("  1. Identificar exatamente o Asset Report.")
    print("  2. Identificar a superfície real do Scanner.")
    print("  3. Identificar mecanismos de Reset.")
    print("  4. Identificar mecanismos de Defaults.")
    print("  5. Somente depois promover mecanismos confirmados para EXEC.")

    print()
    print("=" * 80)
    print("FIM DO PROBE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())