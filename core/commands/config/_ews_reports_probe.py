"""
PRINTER ASSISTANT
MX611 EWS REPORTS PROBE

Mapeia a superfície HTTP/EWS da Lexmark MX611 procurando
interfaces relacionadas a:

- Reports
- Asset Report
- Scanner
- Administration
- Device
- Configuration

IMPORTANTE:

Este módulo é SOMENTE DE CONSULTA.

Não executa:
    SET
    RESET
    DEFAULT
    PRINT
    JOB
    firmware update

Nenhum formulário é enviado.

Nenhum botão é acionado.

O objetivo é descobrir como a interface EWS da própria
impressora representa as operações que queremos controlar.
"""

from __future__ import annotations

import re
import ssl
import sys
import time
from html import unescape
from urllib.parse import urljoin, urlparse

import urllib.request
import urllib.error


# ============================================================
# CONFIGURAÇÃO
# ============================================================

HTTP_TIMEOUT = 5.0

MAX_PAGE_SIZE = 512 * 1024

MAX_PAGES = 30


# ============================================================
# TERMOS DE INTERESSE
# ============================================================

INTEREST_TERMS = [

    "asset",
    "report",
    "reports",
    "scanner",
    "scan",
    "device",
    "administration",
    "administrator",
    "configuration",
    "settings",
    "menu",
    "reset",
    "default",
    "language",
]


# ============================================================
# RESULTADO HTTP
# ============================================================


class PageResult:

    def __init__(
        self,
        url: str,
        status: int,
        content_type: str,
        body: str,
        elapsed: float,
    ):

        self.url = url
        self.status = status
        self.content_type = content_type
        self.body = body
        self.elapsed = elapsed


# ============================================================
# HTTP
# ============================================================


def fetch(
    url: str,
    insecure: bool = False,
) -> PageResult | None:

    started = time.perf_counter()

    try:

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent":
                    "PrinterAssistant-EWS-Probe/1.0"
            },
        )

        context = None

        if url.lower().startswith("https://"):

            if insecure:

                context = ssl._create_unverified_context()

        with urllib.request.urlopen(
            request,
            timeout=HTTP_TIMEOUT,
            context=context,
        ) as response:

            status = response.status

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            body_bytes = response.read(
                MAX_PAGE_SIZE
            )

            body = body_bytes.decode(
                "latin-1",
                errors="replace",
            )

        elapsed = (
            time.perf_counter()
            - started
        )

        return PageResult(
            url=url,
            status=status,
            content_type=content_type,
            body=body,
            elapsed=elapsed,
        )

    except Exception as exc:

        print(
            f"  [ERRO] {url}"
        )

        print(
            f"         {exc}"
        )

        return None


# ============================================================
# LINKS
# ============================================================


def extract_links(
    base_url: str,
    html: str,
) -> list[str]:

    links: set[str] = set()

    patterns = [

        r'href\s*=\s*["\']([^"\']+)["\']',

        r'src\s*=\s*["\']([^"\']+)["\']',

        r'action\s*=\s*["\']([^"\']+)["\']',
    ]

    for pattern in patterns:

        for match in re.findall(
            pattern,
            html,
            flags=re.IGNORECASE,
        ):

            value = unescape(
                match.strip()
            )

            if not value:
                continue

            if value.startswith(
                (
                    "#",
                    "javascript:",
                    "mailto:",
                )
            ):
                continue

            absolute = urljoin(
                base_url,
                value,
            )

            parsed = urlparse(
                absolute
            )

            base = urlparse(
                base_url
            )

            if (
                parsed.hostname
                and parsed.hostname != base.hostname
            ):
                continue

            links.add(
                absolute
            )

    return sorted(links)


# ============================================================
# LIMPEZA HTML
# ============================================================


def html_to_text(
    html: str,
) -> str:

    text = re.sub(
        r"<script\b.*?</script>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<style\b.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = unescape(
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# TERMOS
# ============================================================


def find_terms(
    html: str,
) -> dict[str, list[str]]:

    text = html_to_text(
        html
    )

    lowered = text.lower()

    result: dict[str, list[str]] = {}

    for term in INTEREST_TERMS:

        positions = []

        start = 0

        while True:

            index = lowered.find(
                term,
                start,
            )

            if index == -1:
                break

            begin = max(
                0,
                index - 120,
            )

            end = min(
                len(text),
                index + len(term) + 180,
            )

            positions.append(
                text[begin:end]
            )

            start = (
                index
                + len(term)
            )

            if len(positions) >= 5:
                break

        if positions:

            result[term] = positions

    return result


# ============================================================
# IMPRESSÃO DE RESULTADOS
# ============================================================


def print_page_summary(
    page: PageResult,
) -> None:

    print()

    print(
        "-" * 80
    )

    print(
        f"URL        : {page.url}"
    )

    print(
        f"STATUS     : {page.status}"
    )

    print(
        f"CONTENT    : {page.content_type}"
    )

    print(
        f"BYTES      : {len(page.body.encode('latin-1', errors='replace'))}"
    )

    print(
        f"TEMPO      : {page.elapsed:.3f}s"
    )

    print(
        "-" * 80
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    print("=" * 80)

    print(
        "PRINTER ASSISTANT - MX611 EWS REPORTS PROBE"
    )

    print("=" * 80)

    print()

    print(
        "OBJETIVO:"
    )

    print(
        "Mapear a interface EWS procurando "
        "Reports / Asset Report / Scanner / "
        "Administration."
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

    print(
        "Continuar? [S/N]: ",
        end="",
    )

    if input().strip().upper() != "S":

        print(
            "Operação cancelada."
        )

        return

    # ========================================================
    # HTTP
    # ========================================================

    print()

    print("=" * 80)

    print(
        "1. EWS HTTP"
    )

    print("=" * 80)

    base_http = (
        f"http://{ip}/"
    )

    base_https = (
        f"https://{ip}/"
    )

    pages: dict[str, PageResult] = {}

    print()

    print(
        f"Consultando {base_http}"
    )

    page = fetch(
        base_http
    )

    if page:

        pages[page.url] = page

        print_page_summary(
            page
        )

    # ========================================================
    # HTTPS
    # ========================================================

    print()

    print("=" * 80)

    print(
        "2. EWS HTTPS"
    )

    print("=" * 80)

    print()

    print(
        f"Consultando {base_https}"
    )

    page = fetch(
        base_https,
        insecure=True,
    )

    if page:

        pages[page.url] = page

        print_page_summary(
            page
        )

    # ========================================================
    # DESCOBRIR LINKS
    # ========================================================

    print()

    print("=" * 80)

    print(
        "3. LINKS EWS ENCONTRADOS"
    )

    print("=" * 80)

    discovered: set[str] = set()

    for page in list(
        pages.values()
    ):

        for link in extract_links(
            page.url,
            page.body,
        ):

            discovered.add(
                link
            )

    for link in sorted(
        discovered
    ):

        print(
            f"  {link}"
        )

    print()

    print(
        f"Links encontrados: "
        f"{len(discovered)}"
    )

    # ========================================================
    # CANDIDATOS
    # ========================================================

    print()

    print("=" * 80)

    print(
        "4. CANDIDATOS RELEVANTES"
    )

    print("=" * 80)

    candidates: list[str] = []

    for link in sorted(
        discovered
    ):

        lowered = link.lower()

        if any(
            term in lowered
            for term in INTEREST_TERMS
        ):

            candidates.append(
                link
            )

    for candidate in candidates:

        print(
            f"  [CANDIDATO] {candidate}"
        )

    print()

    print(
        f"Candidatos encontrados: "
        f"{len(candidates)}"
    )

    # ========================================================
    # CONSULTAR CANDIDATOS
    # ========================================================

    print()

    print("=" * 80)

    print(
        "5. CONSULTA DOS CANDIDATOS"
    )

    print("=" * 80)

    visited = set(
        pages.keys()
    )

    queue = list(
        candidates
    )

    count = 0

    while queue and count < MAX_PAGES:

        url = queue.pop(0)

        if url in visited:

            continue

        visited.add(
            url
        )

        print()

        print(
            f"Consultando:"
        )

        print(
            f"  {url}"
        )

        page = fetch(
            url,
            insecure=True,
        )

        if not page:

            continue

        pages[url] = page

        count += 1

        print_page_summary(
            page
        )

        # ----------------------------------------------------
        # Termos relevantes
        # ----------------------------------------------------

        terms = find_terms(
            page.body
        )

        if terms:

            print()

            print(
                "TERMOS RELEVANTES:"
            )

            for term, snippets in terms.items():

                print()

                print(
                    f"[{term}] "
                    f"{len(snippets)} ocorrência(s)"
                )

                for snippet in snippets:

                    print(
                        f"  ...{snippet}..."
                    )

        # ----------------------------------------------------
        # Novos links
        # ----------------------------------------------------

        for link in extract_links(
            page.url,
            page.body,
        ):

            if link not in visited:

                lowered = link.lower()

                if any(
                    term in lowered
                    for term in INTEREST_TERMS
                ):

                    queue.append(
                        link
                    )

    # ========================================================
    # TERMOS NAS PÁGINAS
    # ========================================================

    print()

    print("=" * 80)

    print(
        "6. MAPA DE SUPERFÍCIE"
    )

    print("=" * 80)

    global_matches = {

        term: []

        for term in INTEREST_TERMS
    }

    for url, page in pages.items():

        terms = find_terms(
            page.body
        )

        for term in terms:

            global_matches[
                term
            ].append(
                url
            )

    for term, urls in global_matches.items():

        if not urls:

            continue

        print()

        print(
            f"[{term}]"
        )

        for url in urls:

            print(
                f"  {url}"
            )

    # ========================================================
    # RESULTADO
    # ========================================================

    print()

    print("=" * 80)

    print(
        "RESULTADO DO MAPEAMENTO"
    )

    print("=" * 80)

    print()

    print(
        f"Páginas consultadas : {len(pages)}"
    )

    print(
        f"Links descobertos   : {len(discovered)}"
    )

    print(
        f"Candidatos          : {len(candidates)}"
    )

    print()

    print(
        "IMPORTANTE:"
    )

    print(
        "Este probe não considera nenhum mecanismo "
        "como suportado."
    )

    print(
        "Ele somente identifica onde a função "
        "pode existir na interface EWS."
    )

    print()

    print(
        "=" * 80
    )

    print(
        "FIM DO PROBE"
    )

    print("=" * 80)


if __name__ == "__main__":

    main()