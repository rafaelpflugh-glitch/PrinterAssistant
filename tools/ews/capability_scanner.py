"""
PRINTER ASSISTANT
EWS CAPABILITY SCANNER

Objetivo:
    Transformar o mapa descoberto pelo EWS Discovery Engine
    em um inventário semântico de capacidades da impressora.

IMPORTANTE:
    Este módulo é SOMENTE LEITURA.

    Ele executa apenas HTTP GET.

    NÃO executa:
        POST
        PUT
        DELETE
        RESET
        DEFAULT
        firmware update
        ações PJL
        impressão
        jobs

Arquitetura:

    EWS Discovery
          |
          v
    mapa bruto
          |
          v
    Capability Scanner
          |
          +--> páginas
          +--> links
          +--> forms
          +--> campos
          +--> textos
          +--> classificação
          |
          v
    Capability Map
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DEFAULT_TIMEOUT = 10

DEFAULT_MAX_PAGES = 150

USER_AGENT = (
    "PrinterAssistant/1.0 "
    "EWSCapabilityScanner"
)


# ============================================================
# CLASSIFICAÇÃO SEMÂNTICA
# ============================================================

CATEGORY_RULES = {
    "paper": [
        "paper",
        "papermenu",
        "paperload",
        "papertexture",
        "paperweight",
        "customtypes",
        "customnames",
        "customscan",
        "universal_setup",
        "uni_width",
        "uni_height",
        "tray",
        "cassette",
        "envelope",
        "media",
        "labels",
        "cardstock",
        "papel",
        "bandeja",
        "envelope",
        "etiqueta",
        "cartoes",
    ],

    "scanner": [
        "scanner",
        "scan",
        "digitalizacao",
        "digitalização",
        "customscan",
    ],

    "network": [
        "network",
        "tcp",
        "ip",
        "ipv4",
        "ipv6",
        "ethernet",
        "wifi",
        "wireless",
        "dns",
        "gateway",
        "dhcp",
        "proxy",
        "snmp",
    ],

    "security": [
        "security",
        "secure",
        "password",
        "authentication",
        "auth",
        "certificate",
        "cert",
        "user",
        "admin",
        "administrator",
        "access",
        "seguranca",
        "segurança",
    ],

    "status": [
        "status",
        "state",
        "health",
        "device status",
        "printer status",
        "estado",
        "situacao",
        "situação",
    ],

    "supplies": [
        "supply",
        "supplies",
        "toner",
        "cartridge",
        "cartridge",
        "imaging",
        "photoconductor",
        "drum",
        "waste",
        "fusor",
        "fuser",
        "suprimentos",
        "toner",
        "cartucho",
        "unidade",
    ],

    "maintenance": [
        "maintenance",
        "maint",
        "clean",
        "cleaning",
        "calibration",
        "diagnostic",
        "diagnostics",
        "service",
        "reset",
        "maintenance",
        "limpeza",
        "calibracao",
        "calibração",
        "diagnostico",
        "diagnóstico",
        "servico",
        "serviço",
    ],

    "firmware": [
        "firmware",
        "upgrade",
        "update",
        "flash",
        "firmware",
        "atualizacao",
        "atualização",
    ],

    "copy": [
        "copy",
        "copies",
        "copier",
        "copia",
        "cópia",
        "copies",
    ],

    "print": [
        "print",
        "printing",
        "printer",
        "job",
        "queue",
        "duplex",
        "resolution",
        "orientation",
        "impressao",
        "impressão",
        "trabalho",
        "fila",
    ],

    "fax": [
        "fax",
    ],

    "device": [
        "device",
        "system",
        "general",
        "configuration",
        "config",
        "settings",
        "setting",
        "system",
        "dispositivo",
        "sistema",
        "configuracao",
        "configuração",
        "configurações",
    ],

    "reports": [
        "report",
        "reports",
        "configuration page",
        "menu settings",
        "print report",
        "relatorio",
        "relatório",
        "relatorios",
        "relatórios",
    ],

    "language": [
        "language",
        "langbar",
        "locale",
        "idioma",
        "lingua",
        "língua",
    ],
}


# ============================================================
# PALAVRAS DE AÇÃO
# ============================================================

ACTION_TERMS = [
    "save",
    "apply",
    "submit",
    "change",
    "set",
    "update",
    "reset",
    "restore",
    "restart",
    "reboot",
    "delete",
    "clear",
    "print",
    "start",
    "stop",
    "enable",
    "disable",
    "salvar",
    "aplicar",
    "alterar",
    "atualizar",
    "reiniciar",
    "restaurar",
    "excluir",
    "limpar",
    "imprimir",
    "iniciar",
    "parar",
    "ativar",
    "desativar",
]


# ============================================================
# PALAVRAS DE LEITURA
# ============================================================

READ_TERMS = [
    "status",
    "information",
    "information",
    "details",
    "serial",
    "firmware",
    "version",
    "model",
    "device",
    "supply",
    "toner",
    "level",
    "capacity",
    "estado",
    "informacao",
    "informação",
    "detalhes",
    "numero de serie",
    "número de série",
    "versao",
    "versão",
    "modelo",
    "nivel",
    "nível",
]


# ============================================================
# RESULTADOS
# ============================================================

@dataclass
class FieldInfo:
    name: str
    field_type: str
    value: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class FormInfo:
    action: str
    method: str
    fields: list[FieldInfo] = field(default_factory=list)


@dataclass
class PageCapability:
    url: str
    path: str
    status_code: int
    bytes: int

    title: str = ""

    categories: list[str] = field(
        default_factory=list
    )

    capability_class: str = "unknown"

    forms: int = 0
    fields: int = 0

    selects: int = 0
    text_inputs: int = 0
    checkboxes: int = 0
    radios: int = 0
    hidden_inputs: int = 0
    textareas: int = 0

    buttons: int = 0
    links: int = 0

    get_forms: int = 0
    post_forms: int = 0

    action_terms: list[str] = field(
        default_factory=list
    )

    read_terms: list[str] = field(
        default_factory=list
    )

    discovered_links: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )


# ============================================================
# SCANNER
# ============================================================

class EWSCapabilityScanner:

    def __init__(
        self,
        printer_ip: str,
        timeout: int = DEFAULT_TIMEOUT,
        max_pages: int = DEFAULT_MAX_PAGES,
    ):
        self.printer_ip = printer_ip

        self.base_url = (
            f"http://{printer_ip}/"
        )

        self.timeout = timeout
        self.max_pages = max_pages

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT
        })

        self.visited: set[str] = set()

        self.queue = deque()

        self.pages: list[PageCapability] = []

        self.errors: list[dict[str, str]] = []

        self.category_counter = Counter()

        self.class_counter = Counter()

    # ========================================================
    # URL
    # ========================================================

    def normalize_url(
        self,
        url: str,
        base: str | None = None,
    ) -> str:

        if not url:
            return ""

        if base is None:
            base = self.base_url

        absolute = urljoin(
            base,
            url,
        )

        parsed = urlparse(
            absolute
        )

        if parsed.scheme not in {
            "http",
            "https",
        }:
            return ""

        if parsed.hostname != self.printer_ip:
            return ""

        # Remove fragment.
        normalized = parsed._replace(
            fragment=""
        ).geturl()

        return normalized

    # ========================================================
    # PATH
    # ========================================================

    @staticmethod
    def url_path(
        url: str,
    ) -> str:

        parsed = urlparse(url)

        return parsed.path or "/"

    # ========================================================
    # MAP EXTRACTION
    # ========================================================

    def extract_urls_from_json(
        self,
        data: Any,
    ) -> set[str]:

        urls: set[str] = set()

        def walk(
            value: Any,
        ):

            if isinstance(value, str):

                if (
                    value.startswith(
                        "http://"
                    )
                    or value.startswith(
                        "https://"
                    )
                ):
                    normalized = (
                        self.normalize_url(
                            value
                        )
                    )

                    if normalized:
                        urls.add(normalized)

                elif value.startswith(
                    "/cgi-bin/"
                ):
                    normalized = (
                        self.normalize_url(
                            value
                        )
                    )

                    if normalized:
                        urls.add(normalized)

                return

            if isinstance(value, dict):

                for item in value.values():
                    walk(item)

                return

            if isinstance(value, list):

                for item in value:
                    walk(item)

        walk(data)

        return urls

    # ========================================================
    # MAP LOAD
    # ========================================================

    def load_discovery_map(
        self,
        map_path: Path,
    ) -> set[str]:

        if not map_path.exists():

            print(
                f"[AVISO] Mapa não encontrado:"
            )

            print(
                f"        {map_path}"
            )

            return set()

        print(
            f"[OK] Mapa Discovery encontrado:"
        )

        print(
            f"     {map_path}"
        )

        try:

            with map_path.open(
                "r",
                encoding="utf-8",
            ) as f:

                data = json.load(f)

        except Exception as exc:

            print(
                f"[ERRO] Falha lendo mapa: {exc}"
            )

            return set()

        urls = (
            self.extract_urls_from_json(
                data
            )
        )

        print(
            f"[OK] URLs extraídas do mapa: "
            f"{len(urls)}"
        )

        return urls

    # ========================================================
    # PAGE GET
    # ========================================================

    def fetch(
        self,
        url: str,
    ):

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        return response

    # ========================================================
    # CATEGORY
    # ========================================================

    def classify_categories(
        self,
        url: str,
        title: str,
        text: str,
    ) -> list[str]:

        haystack = (
            f"{url}\n"
            f"{title}\n"
            f"{text}"
        ).lower()

        scores: Counter = Counter()

        for category, terms in (
            CATEGORY_RULES.items()
        ):

            for term in terms:

                if term.lower() in haystack:

                    scores[category] += 1

        if not scores:
            return ["other"]

        highest = max(
            scores.values()
        )

        # Mantém categorias com pelo menos
        # 25% da maior pontuação.
        threshold = max(
            1,
            int(highest * 0.25)
        )

        categories = [
            category
            for category, score
            in scores.items()
            if score >= threshold
        ]

        categories.sort(
            key=lambda x: (
                -scores[x],
                x,
            )
        )

        return categories

    # ========================================================
    # CAPABILITY CLASS
    # ========================================================

    def classify_capability(
        self,
        forms: list[FormInfo],
        action_terms: list[str],
        read_terms: list[str],
    ) -> str:

        has_post = any(
            form.method == "POST"
            for form in forms
        )

        has_fields = any(
            form.fields
            for form in forms
        )

        has_actions = bool(
            action_terms
        )

        has_read = bool(
            read_terms
        )

        if has_post and has_fields:

            if has_actions:

                return "configuration_or_action"

            return "configuration"

        if has_fields:

            return "configuration_candidate"

        if has_read:

            return "read"

        return "navigation_or_information"

    # ========================================================
    # TERMS
    # ========================================================

    @staticmethod
    def find_terms(
        text: str,
        terms: list[str],
    ) -> list[str]:

        lowered = text.lower()

        found = []

        for term in terms:

            if term.lower() in lowered:

                found.append(term)

        return sorted(
            set(found)
        )

    # ========================================================
    # PARSE PAGE
    # ========================================================

    def parse_page(
        self,
        response,
    ) -> PageCapability:

        url = response.url

        path = self.url_path(
            url
        )

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        title_element = soup.find(
            "title"
        )

        title = ""

        if title_element:

            title = title_element.get_text(
                " ",
                strip=True
            )

        visible_text = soup.get_text(
            " ",
            strip=True
        )

        forms: list[FormInfo] = []

        for form in soup.find_all(
            "form"
        ):

            action = (
                form.get("action")
                or url
            )

            action = urljoin(
                url,
                action
            )

            method = (
                form.get("method")
                or "GET"
            ).upper()

            fields: list[FieldInfo] = []

            for select in form.find_all(
                "select"
            ):

                name = select.get(
                    "name"
                )

                if not name:
                    continue

                options = []

                for option in select.find_all(
                    "option"
                ):

                    option_value = (
                        option.get(
                            "value",
                            ""
                        )
                    )

                    option_text = (
                        option.get_text(
                            " ",
                            strip=True
                        )
                    )

                    options.append(
                        f"{option_value}={option_text}"
                    )

                fields.append(
                    FieldInfo(
                        name=name,
                        field_type="select",
                        value="",
                        options=options,
                    )
                )

            for element in form.find_all(
                "input"
            ):

                input_type = (
                    element.get("type")
                    or "text"
                ).lower()

                name = element.get(
                    "name"
                )

                if not name:
                    continue

                if input_type in {
                    "submit",
                    "reset",
                    "button",
                }:
                    continue

                value = element.get(
                    "value",
                    ""
                )

                fields.append(
                    FieldInfo(
                        name=name,
                        field_type=input_type,
                        value=value,
                    )
                )

            for textarea in form.find_all(
                "textarea"
            ):

                name = textarea.get(
                    "name"
                )

                if not name:
                    continue

                fields.append(
                    FieldInfo(
                        name=name,
                        field_type="textarea",
                        value=textarea.get_text(
                            " ",
                            strip=True
                        ),
                    )
                )

            forms.append(
                FormInfo(
                    action=action,
                    method=method,
                    fields=fields,
                )
            )

        # ----------------------------------------------------
        # CONTROLES
        # ----------------------------------------------------

        selects = sum(
            1
            for form in forms
            for field in form.fields
            if field.field_type == "select"
        )

        text_inputs = sum(
            1
            for form in forms
            for field in form.fields
            if field.field_type == "text"
        )

        checkboxes = sum(
            1
            for form in forms
            for field in form.fields
            if field.field_type == "checkbox"
        )

        radios = sum(
            1
            for form in forms
            for field in form.fields
            if field.field_type == "radio"
        )

        hidden_inputs = sum(
            1
            for form in forms
            for field in form.fields
            if field.field_type == "hidden"
        )

        textareas = sum(
            1
            for form in forms
            for field in form.fields
            if field.field_type == "textarea"
        )

        buttons = len(
            soup.find_all(
                [
                    "button",
                ]
            )
        )

        links = soup.find_all(
            "a",
            href=True
        )

        discovered_links = []

        for link in links:

            href = link.get(
                "href"
            )

            normalized = (
                self.normalize_url(
                    href,
                    base=url,
                )
            )

            if normalized:

                discovered_links.append(
                    normalized
                )

        discovered_links = sorted(
            set(discovered_links)
        )

        action_terms = self.find_terms(
            f"{url}\n{title}\n{visible_text}",
            ACTION_TERMS,
        )

        read_terms = self.find_terms(
            f"{url}\n{title}\n{visible_text}",
            READ_TERMS,
        )

        categories = (
            self.classify_categories(
                url,
                title,
                visible_text,
            )
        )

        capability_class = (
            self.classify_capability(
                forms,
                action_terms,
                read_terms,
            )
        )

        return PageCapability(
            url=url,
            path=path,
            status_code=response.status_code,
            bytes=len(response.content),
            title=title,
            categories=categories,
            capability_class=capability_class,
            forms=len(forms),
            fields=sum(
                len(form.fields)
                for form in forms
            ),
            selects=selects,
            text_inputs=text_inputs,
            checkboxes=checkboxes,
            radios=radios,
            hidden_inputs=hidden_inputs,
            textareas=textareas,
            buttons=buttons,
            links=len(discovered_links),
            get_forms=sum(
                1
                for form in forms
                if form.method == "GET"
            ),
            post_forms=sum(
                1
                for form in forms
                if form.method == "POST"
            ),
            action_terms=action_terms,
            read_terms=read_terms,
            discovered_links=discovered_links,
        )

    # ========================================================
    # QUEUE
    # ========================================================

    def enqueue(
        self,
        url: str,
    ):

        normalized = (
            self.normalize_url(
                url
            )
        )

        if not normalized:
            return

        if normalized in self.visited:
            return

        if normalized in self.queue:
            return

        self.queue.append(
            normalized
        )

    # ========================================================
    # SCAN
    # ========================================================

    def scan(
        self,
        seed_urls: set[str],
    ):

        for url in sorted(
            seed_urls
        ):

            self.enqueue(
                url
            )

        # Sempre incluir home.
        self.enqueue(
            self.base_url
        )

        print()
        print("=" * 72)
        print(
            "EWS CAPABILITY SCANNER"
        )
        print("=" * 72)

        print()
        print(
            f"Impressora : "
            f"{self.printer_ip}"
        )

        print(
            f"Fila inicial : "
            f"{len(self.queue)}"
        )

        print(
            f"Limite páginas : "
            f"{self.max_pages}"
        )

        print()

        while (
            self.queue
            and len(self.pages)
            < self.max_pages
        ):

            url = self.queue.popleft()

            if url in self.visited:
                continue

            self.visited.add(
                url
            )

            number = len(
                self.pages
            ) + 1

            print(
                f"[{number:04d}] "
                f"{url}"
            )

            started = time.perf_counter()

            try:

                response = self.fetch(
                    url
                )

                elapsed = (
                    time.perf_counter()
                    - started
                )

                print(
                    f"      HTTP "
                    f"{response.status_code} "
                    f"- "
                    f"{len(response.content)} "
                    f"bytes "
                    f"({elapsed:.3f}s)"
                )

                if response.status_code != 200:

                    self.errors.append({
                        "url": url,
                        "error": (
                            f"HTTP "
                            f"{response.status_code}"
                        ),
                    })

                    continue

                capability = (
                    self.parse_page(
                        response
                    )
                )

                self.pages.append(
                    capability
                )

                for category in (
                    capability.categories
                ):

                    self.category_counter[
                        category
                    ] += 1

                self.class_counter[
                    capability.capability_class
                ] += 1

                print(
                    f"      "
                    f"{capability.capability_class}"
                )

                print(
                    f"      categorias: "
                    f"{', '.join(capability.categories)}"
                )

                print(
                    f"      forms={capability.forms} "
                    f"fields={capability.fields} "
                    f"links={capability.links}"
                )

                # Expansão controlada.
                for link in (
                    capability.discovered_links
                ):

                    self.enqueue(
                        link
                    )

            except requests.RequestException as exc:

                print(
                    f"      [ERRO HTTP] "
                    f"{exc}"
                )

                self.errors.append({
                    "url": url,
                    "error": str(exc),
                })

            except Exception as exc:

                print(
                    f"      [ERRO] "
                    f"{exc}"
                )

                self.errors.append({
                    "url": url,
                    "error": str(exc),
                })

        print()
        print("=" * 72)
        print(
            "CAPABILITY SCAN FINALIZADO"
        )
        print("=" * 72)

        print()
        print(
            f"Páginas analisadas : "
            f"{len(self.pages)}"
        )

        print(
            f"URLs visitadas     : "
            f"{len(self.visited)}"
        )

        print(
            f"URLs restantes     : "
            f"{len(self.queue)}"
        )

        print(
            f"Erros              : "
            f"{len(self.errors)}"
        )

        self.print_summary()

    # ========================================================
    # SUMMARY
    # ========================================================

    def print_summary(
        self,
    ):

        print()
        print(
            "CLASSIFICAÇÃO:"
        )

        for name, count in (
            self.class_counter.most_common()
        ):

            print(
                f"  {name:<28} "
                f"{count}"
            )

        print()
        print(
            "CATEGORIAS:"
        )

        for name, count in (
            self.category_counter.most_common()
        ):

            print(
                f"  {name:<28} "
                f"{count}"
            )

        print()
        print(
            "PÁGINAS COM POST:"
        )

        post_pages = [
            page
            for page in self.pages
            if page.post_forms > 0
        ]

        for page in post_pages:

            print(
                f"  {page.path}"
            )

            print(
                f"      "
                f"{', '.join(page.categories)}"
            )

            print(
                f"      "
                f"forms={page.forms} "
                f"fields={page.fields}"
            )

        print()
        print(
            "PÁGINAS DE LEITURA:"
        )

        read_pages = [
            page
            for page in self.pages
            if page.capability_class == "read"
        ]

        for page in read_pages:

            print(
                f"  {page.path}"
            )

    # ========================================================
    # JSON
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "scanner": {
                "name": (
                    "EWS Capability Scanner"
                ),
                "version": "1.0",
                "read_only": True,
                "http_methods_used": [
                    "GET"
                ],
                "printer_ip": self.printer_ip,
                "max_pages": self.max_pages,
            },

            "summary": {
                "pages": len(
                    self.pages
                ),
                "visited": len(
                    self.visited
                ),
                "remaining_queue": len(
                    self.queue
                ),
                "errors": len(
                    self.errors
                ),
                "classification": dict(
                    self.class_counter
                ),
                "categories": dict(
                    self.category_counter
                ),
            },

            "pages": [
                asdict(page)
                for page in self.pages
            ],

            "errors": self.errors,
        }


# ============================================================
# IP
# ============================================================

def safe_ip_filename(
    ip: str,
) -> str:

    return re.sub(
        r"[^0-9A-Za-z_.-]",
        "_",
        ip,
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Printer Assistant "
            "EWS Capability Scanner"
        )
    )

    parser.add_argument(
        "ip",
        help="IP da impressora",
    )

    parser.add_argument(
        "--map",
        dest="map_path",
        default=None,
        help=(
            "Mapa Discovery JSON "
            "opcional"
        ),
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=(
            "Número máximo de páginas "
            "a analisar"
        ),
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=(
            "Timeout HTTP em segundos"
        ),
    )

    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Arquivo JSON de saída"
        ),
    )

    args = parser.parse_args()

    root = Path.cwd()

    # --------------------------------------------------------
    # MAPA DISCOVERY
    # --------------------------------------------------------

    if args.map_path:

        map_path = Path(
            args.map_path
        )

    else:

        safe_ip = safe_ip_filename(
            args.ip
        )

        map_path = (
            root
            / "ews"
            / "maps"
            / f"ews_{safe_ip}.json"
        )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    if args.output:

        output_path = Path(
            args.output
        )

    else:

        safe_ip = safe_ip_filename(
            args.ip
        )

        output_path = (
            root
            / "ews"
            / "capabilities"
            / f"capabilities_{safe_ip}.json"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # SCANNER
    # --------------------------------------------------------

    scanner = EWSCapabilityScanner(
        printer_ip=args.ip,
        timeout=args.timeout,
        max_pages=args.max_pages,
    )

    seed_urls = (
        scanner.load_discovery_map(
            map_path
        )
    )

    scanner.scan(
        seed_urls
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    result = scanner.to_dict()

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 72)
    print(
        "CAPABILITY MAP SALVO"
    )
    print("=" * 72)

    print()
    print(
        f"Arquivo:"
    )

    print(
        f"  {output_path}"
    )

    print()

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )