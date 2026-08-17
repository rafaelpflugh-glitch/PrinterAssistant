"""
PRINTER ASSISTANT
MX611 EWS SURFACE PROBE

Probe somente de CONSULTA da superfície EWS da Lexmark MX611dhe.

OBJETIVO
--------
Explorar as páginas que a própria impressora expõe a partir da
interface EWS conhecida:

    /
    /cgi-bin/dynamic/left_bar.html
    /cgi-bin/dynamic/printer/PrinterStatus.html
    /cgi-bin/dynamic/topbar.html
    /cgi-bin/dynamic/printer/langbar.html

O probe também procura links, formulários, actions, referências
JavaScript e termos relacionados a:

    Reports
    Asset
    Scanner
    Administration
    Configuration
    Reset
    Defaults
    Device
    Supplies
    Maintenance
    Network
    Settings

REGRAS DE SEGURANÇA
-------------------
Este módulo:

    NÃO envia GET para caminhos descobertos automaticamente
    NÃO envia POST
    NÃO envia PUT
    NÃO envia DELETE
    NÃO submete formulários
    NÃO executa JavaScript
    NÃO envia PJL
    NÃO envia SET
    NÃO envia RESET
    NÃO envia DEFAULT
    NÃO solicita impressão
    NÃO altera configuração

Somente consulta páginas explicitamente definidas neste probe.

IMPORTANTE
----------
Encontrar uma palavra, link ou formulário NÃO significa que a
operação está suportada.

Este módulo apenas mapeia a superfície EWS.

Nada encontrado aqui será automaticamente promovido para EXEC.
"""

from __future__ import annotations

import re
import ssl
import time
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import urljoin, urlparse

import urllib.error
import urllib.request


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TIMEOUT = 5.0

MAX_BYTES = 512_000

SCHEMES = (
    "http",
    "https",
)

KNOWN_PATHS = (
    "/",
    "/cgi-bin/dynamic/left_bar.html",
    "/cgi-bin/dynamic/printer/PrinterStatus.html",
    "/cgi-bin/dynamic/topbar.html",
    "/cgi-bin/dynamic/printer/langbar.html",
)

RELEVANT_TERMS = (
    "report",
    "reports",
    "asset",
    "asset report",
    "scanner",
    "scan",
    "administration",
    "admin",
    "configuration",
    "config",
    "reset",
    "default",
    "defaults",
    "device",
    "supplies",
    "supply",
    "maintenance",
    "network",
    "settings",
    "status",
    "menu",
    "printer",
)


# ============================================================
# RESULTADO HTTP
# ============================================================


@dataclass
class PageResult:

    url: str

    status: int

    content_type: str

    body: str

    elapsed: float

    error: str = ""


# ============================================================
# UTILIDADES
# ============================================================


def separator(char: str = "=") -> None:

    print(char * 80)


def normalize_text(text: str) -> str:

    text = unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def clean_html_for_search(html: str) -> str:

    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    return normalize_text(text)


def extract_urls(
    html: str,
    base_url: str,
) -> list[str]:

    found: list[str] = []

    # --------------------------------------------------------
    # href
    # --------------------------------------------------------

    for match in re.finditer(
        r"""href\s*=\s*["']([^"']+)["']""",
        html,
        flags=re.IGNORECASE,
    ):

        raw = unescape(
            match.group(1).strip()
        )

        if not raw:
            continue

        if raw.startswith(
            (
                "#",
                "javascript:",
                "mailto:",
            )
        ):
            continue

        url = urljoin(
            base_url,
            raw,
        )

        if url not in found:

            found.append(url)

    # --------------------------------------------------------
    # src
    # --------------------------------------------------------

    for match in re.finditer(
        r"""src\s*=\s*["']([^"']+)["']""",
        html,
        flags=re.IGNORECASE,
    ):

        raw = unescape(
            match.group(1).strip()
        )

        if not raw:
            continue

        if raw.startswith(
            (
                "#",
                "javascript:",
                "mailto:",
            )
        ):
            continue

        url = urljoin(
            base_url,
            raw,
        )

        if url not in found:

            found.append(url)

    return found


def extract_forms(
    html: str,
    base_url: str,
) -> list[dict[str, str]]:

    forms: list[dict[str, str]] = []

    pattern = re.compile(
        r"<form\b([^>]*)>",
        flags=re.IGNORECASE,
    )

    for match in pattern.finditer(html):

        attrs = match.group(1)

        action_match = re.search(
            r"""action\s*=\s*["']([^"']*)["']""",
            attrs,
            flags=re.IGNORECASE,
        )

        method_match = re.search(
            r"""method\s*=\s*["']([^"']*)["']""",
            attrs,
            flags=re.IGNORECASE,
        )

        action = (
            action_match.group(1)
            if action_match
            else ""
        )

        method = (
            method_match.group(1)
            if method_match
            else "GET"
        )

        forms.append(
            {
                "action": urljoin(
                    base_url,
                    action,
                ),
                "method": method.upper(),
            }
        )

    return forms


def extract_input_names(
    html: str,
) -> list[str]:

    names: list[str] = []

    for match in re.finditer(
        r"""<input\b([^>]*)>""",
        html,
        flags=re.IGNORECASE,
    ):

        attrs = match.group(1)

        name_match = re.search(
            r"""name\s*=\s*["']([^"']+)["']""",
            attrs,
            flags=re.IGNORECASE,
        )

        if name_match:

            name = unescape(
                name_match.group(1)
            )

            if name not in names:

                names.append(name)

    return names


def find_term_occurrences(
    html: str,
    term: str,
) -> list[str]:

    occurrences: list[str] = []

    pattern = re.compile(
        re.escape(term),
        flags=re.IGNORECASE,
    )

    for match in pattern.finditer(html):

        start = max(
            0,
            match.start() - 140,
        )

        end = min(
            len(html),
            match.end() + 180,
        )

        snippet = html[
            start:end
        ]

        snippet = normalize_text(
            snippet
        )

        if snippet not in occurrences:

            occurrences.append(
                snippet
            )

        if len(occurrences) >= 3:

            break

    return occurrences


# ============================================================
# HTTP
# ============================================================


def make_opener() -> urllib.request.OpenerDirector:

    context = ssl._create_unverified_context()

    https_handler = (
        urllib.request.HTTPSHandler(
            context=context
        )
    )

    return urllib.request.build_opener(
        https_handler
    )


def fetch_page(
    opener: urllib.request.OpenerDirector,
    url: str,
) -> PageResult:

    started = time.perf_counter()

    request = urllib.request.Request(
        url=url,
        method="GET",
        headers={
            "User-Agent":
                "PrinterAssistant-EWS-Probe/1.0",
            "Accept":
                "text/html,text/plain,*/*",
        },
    )

    try:

        with opener.open(
            request,
            timeout=TIMEOUT,
        ) as response:

            status = getattr(
                response,
                "status",
                200,
            )

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            data = response.read(
                MAX_BYTES + 1
            )

            if len(data) > MAX_BYTES:

                data = data[
                    :MAX_BYTES
                ]

            charset = "latin-1"

            charset_match = re.search(
                r"charset\s*=\s*['\"]?([\w-]+)",
                content_type,
                flags=re.IGNORECASE,
            )

            if charset_match:

                charset = (
                    charset_match.group(1)
                )

            try:

                body = data.decode(
                    charset,
                    errors="replace",
                )

            except LookupError:

                body = data.decode(
                    "latin-1",
                    errors="replace",
                )

            elapsed = (
                time.perf_counter()
                - started
            )

            return PageResult(
                url=url,
                status=int(status),
                content_type=content_type,
                body=body,
                elapsed=elapsed,
            )

    except urllib.error.HTTPError as exc:

        elapsed = (
            time.perf_counter()
            - started
        )

        return PageResult(
            url=url,
            status=int(
                getattr(
                    exc,
                    "code",
                    0,
                )
            ),
            content_type="",
            body="",
            elapsed=elapsed,
            error=str(exc),
        )

    except Exception as exc:

        elapsed = (
            time.perf_counter()
            - started
        )

        return PageResult(
            url=url,
            status=0,
            content_type="",
            body="",
            elapsed=elapsed,
            error=str(exc),
        )


# ============================================================
# EXIBIÇÃO
# ============================================================


def print_page_header(
    result: PageResult,
) -> None:

    separator("-")

    print(
        f"URL        : {result.url}"
    )

    print(
        f"STATUS     : {result.status}"
    )

    print(
        f"CONTENT    : {result.content_type}"
    )

    print(
        f"BYTES      : {len(result.body.encode('latin-1', errors='replace'))}"
    )

    print(
        f"TEMPO      : {result.elapsed:.3f}s"
    )

    if result.error:

        print(
            f"ERRO       : {result.error}"
        )

    separator("-")


def print_links(
    links: Iterable[str],
    base_url: str,
) -> None:

    links = list(links)

    if not links:

        print(
            "  Nenhum link/recurso encontrado."
        )

        return

    for url in links:

        parsed = urlparse(url)

        if parsed.netloc:

            # Só exibimos.
            # NÃO seguimos automaticamente.
            print(
                f"  {url}"
            )

        else:

            print(
                f"  {url}"
            )


def print_forms(
    forms: list[dict[str, str]],
) -> None:

    if not forms:

        print(
            "  Nenhum formulário encontrado."
        )

        return

    for index, form in enumerate(
        forms,
        start=1,
    ):

        print(
            f"  FORM {index}"
        )

        print(
            f"    method : {form['method']}"
        )

        print(
            f"    action : {form['action']}"
        )


# ============================================================
# ANÁLISE
# ============================================================


def analyze_page(
    result: PageResult,
) -> None:

    html = result.body

    text = clean_html_for_search(
        html
    )

    print()

    print(
        "TERMOS RELEVANTES"
    )

    separator("-")

    found_any = False

    for term in RELEVANT_TERMS:

        occurrences = (
            find_term_occurrences(
                text,
                term,
            )
        )

        if not occurrences:

            continue

        found_any = True

        print(
            f"[{term}] "
            f"{len(occurrences)} ocorrência(s)"
        )

        for occurrence in occurrences:

            print(
                f"  ...{occurrence}..."
            )

    if not found_any:

        print(
            "Nenhum termo relevante encontrado."
        )

    print()

    print(
        "LINKS / RECURSOS"
    )

    separator("-")

    links = extract_urls(
        html,
        result.url,
    )

    print_links(
        links,
        result.url,
    )

    print()

    print(
        "FORMULÁRIOS"
    )

    separator("-")

    forms = extract_forms(
        html,
        result.url,
    )

    print_forms(
        forms
    )

    print()

    print(
        "CAMPOS DE FORMULÁRIO"
    )

    separator("-")

    names = extract_input_names(
        html
    )

    if names:

        for name in names:

            print(
                f"  {name}"
            )

    else:

        print(
            "  Nenhum campo encontrado."
        )


# ============================================================
# MAPA GLOBAL
# ============================================================


def build_surface_map(
    results: list[PageResult],
) -> None:

    separator("=")

    print(
        "MAPA DA SUPERFÍCIE EWS"
    )

    separator("=")

    all_links: list[str] = []

    all_terms: dict[str, int] = {}

    all_forms: list[dict[str, str]] = []

    for result in results:

        if result.status != 200:

            continue

        links = extract_urls(
            result.body,
            result.url,
        )

        for link in links:

            if link not in all_links:

                all_links.append(
                    link
                )

        text = clean_html_for_search(
            result.body
        )

        for term in RELEVANT_TERMS:

            count = len(
                re.findall(
                    re.escape(term),
                    text,
                    flags=re.IGNORECASE,
                )
            )

            if count:

                all_terms[term] = (
                    all_terms.get(
                        term,
                        0,
                    )
                    + count
                )

        all_forms.extend(
            extract_forms(
                result.body,
                result.url,
            )
        )

    print()

    print(
        "PÁGINAS CONSULTADAS"
    )

    for result in results:

        print(
            f"  [{result.status}] "
            f"{result.url}"
        )

    print()

    print(
        "TERMOS ENCONTRADOS"
    )

    if all_terms:

        for term, count in sorted(
            all_terms.items()
        ):

            print(
                f"  {term:<20} {count}"
            )

    else:

        print(
            "  Nenhum."
        )

    print()

    print(
        "LINKS / RECURSOS DESCOBERTOS"
    )

    if all_links:

        for link in sorted(
            all_links
        ):

            print(
                f"  {link}"
            )

    else:

        print(
            "  Nenhum."
        )

    print()

    print(
        "FORMULÁRIOS DESCOBERTOS"
    )

    if all_forms:

        for index, form in enumerate(
            all_forms,
            start=1,
        ):

            print(
                f"  FORM {index}"
            )

            print(
                f"    {form['method']} "
                f"{form['action']}"
            )

    else:

        print(
            "  Nenhum."
        )

    print()

    print(
        "OBSERVAÇÃO DE SEGURANÇA"
    )

    separator("-")

    print(
        "Links encontrados não foram seguidos automaticamente."
    )

    print(
        "Formulários encontrados NÃO foram submetidos."
    )

    print(
        "Nenhuma operação de alteração foi executada."
    )

    print(
        "Nenhuma página foi solicitada para impressão."
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    separator("=")

    print(
        "PRINTER ASSISTANT - MX611 EWS SURFACE PROBE"
    )

    separator("=")

    print()

    print(
        "OBJETIVO:"
    )

    print(
        "Mapear a superfície EWS já descoberta na MX611."
    )

    print()

    print(
        "PÁGINAS CONSULTADAS:"
    )

    for path in KNOWN_PATHS:

        print(
            f"  {path}"
        )

    print()

    print(
        "ESTE TESTE É SOMENTE DE CONSULTA."
    )

    print(
        "Nenhum SET será enviado."
    )

    print(
        "Nenhum RESET será enviado."
    )

    print(
        "Nenhum DEFAULT será enviado."
    )

    print(
        "Nenhum PRINT será solicitado."
    )

    print(
        "Nenhum formulário será submetido."
    )

    print(
        "Nenhum link descoberto será seguido automaticamente."
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

    print()

    answer = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if answer != "S":

        print(
            "Operação cancelada."
        )

        return

    opener = make_opener()

    results: list[PageResult] = []

    # ========================================================
    # HTTP E HTTPS
    # ========================================================

    for scheme in SCHEMES:

        separator("=")

        print(
            f"SUPERFÍCIE {scheme.upper()}"
        )

        separator("=")

        for path in KNOWN_PATHS:

            url = (
                f"{scheme}://"
                f"{ip}"
                f"{path}"
            )

            print()

            print(
                f"Consultando {url}"
            )

            result = fetch_page(
                opener,
                url,
            )

            results.append(
                result
            )

            print_page_header(
                result
            )

            if result.status == 200:

                analyze_page(
                    result
                )

    # ========================================================
    # MAPA FINAL
    # ========================================================

    build_surface_map(
        results
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    separator("=")

    print(
        "RESULTADO DO MAPEAMENTO"
    )

    separator("=")

    successful = [
        result
        for result in results
        if result.status == 200
    ]

    print()

    print(
        f"URLs consultadas : {len(results)}"
    )

    print(
        f"URLs respondendo : {len(successful)}"
    )

    print()

    print(
        "IMPORTANTE:"
    )

    print(
        "Este probe não considera nenhum mecanismo como suportado."
    )

    print(
        "Somente a confirmação do efeito real permitirá promover"
    )

    print(
        "uma operação para EXEC no Operation Registry."
    )

    print()

    print(
        "PRÓXIMA ETAPA:"
    )

    print(
        "Usar o mapa obtido para investigar:"
    )

    print(
        "  1. Asset Report"
    )

    print(
        "  2. Scanner enable/disable"
    )

    print(
        "  3. Printer Reset"
    )

    print(
        "  4. Printer Defaults"
    )

    separator("=")

    print(
        "FIM DO PROBE"
    )

    separator("=")


if __name__ == "__main__":

    main()