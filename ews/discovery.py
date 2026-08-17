import json
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .model import Page, Form, Field, Option
from .mapper import build_knowledge, save_knowledge


class EWSDiscovery:

    def __init__(
        self,
        printer_ip,
        output_dir="ews",
        timeout=10,
        max_pages=500,
    ):

        self.printer_ip = printer_ip
        self.base_url = f"http://{printer_ip}"

        self.output_dir = Path(output_dir)

        self.raw_dir = self.output_dir / "raw"
        self.map_dir = self.output_dir / "maps"
        self.knowledge_dir = self.output_dir / "knowledge"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.map_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self.max_pages = max_pages

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "PrinterAssistant-EWS-Discovery/1.0"
            )
        })

        self.visited = set()
        self.pages = []

    # ========================================================
    # URL
    # ========================================================

    def make_url(self, path):

        if path.startswith("http://"):
            return path

        if path.startswith("https://"):
            return path

        if not path.startswith("/"):
            path = "/" + path

        return self.base_url + path

    # ========================================================
    # SEGURANÇA: SÓ DENTRO DA IMPRESSORA
    # ========================================================

    def allowed_url(self, url):

        parsed = urlparse(url)

        base = urlparse(self.base_url)

        return (
            parsed.hostname == base.hostname
            and parsed.scheme in ("http", "https")
        )

    # ========================================================
    # NOME DO ARQUIVO
    # ========================================================

    def safe_filename(self, url):

        parsed = urlparse(url)

        path = parsed.path.strip("/")

        if not path:
            return "index"

        name = path.replace("/", "_")

        name = name.replace("\\", "_")

        return name[:200]

    # ========================================================
    # DOWNLOAD
    # ========================================================

    def fetch(self, url):

        try:

            response = self.session.get(
                url,
                timeout=self.timeout,
            )

            return response

        except Exception as e:

            print(f"[ERRO] {url}")
            print(f"       {e}")

            return None

    # ========================================================
    # PARSER
    # ========================================================

    def parse_page(self, url, response):

        content = response.text

        soup = BeautifulSoup(
            content,
            "html.parser",
        )

        title = ""

        if soup.title:
            title = soup.title.get_text(
                " ",
                strip=True,
            )

        links = []

        for tag in soup.find_all("a", href=True):

            href = tag.get("href")

            absolute = urljoin(
                url,
                href,
            )

            if self.allowed_url(absolute):

                links.append(absolute)

        forms = []

        for html_form in soup.find_all("form"):

            action = html_form.get("action") or url

            action = urljoin(
                url,
                action,
            )

            method = (
                html_form.get("method")
                or "GET"
            ).upper()

            form = Form(
                page_url=url,
                action=action,
                method=method,
            )

            # ------------------------------------------------
            # SELECT
            # ------------------------------------------------

            for select in html_form.find_all("select"):

                name = select.get("name")

                field_id = select.get("id")

                field = Field(
                    field_type="select",
                    name=name,
                    field_id=field_id,
                )

                selected_value = None

                for option in select.find_all("option"):

                    value = option.get("value", "")

                    text = option.get_text(
                        " ",
                        strip=True,
                    )

                    selected = option.has_attr(
                        "selected"
                    )

                    if selected:
                        selected_value = value

                    field.options.append(
                        Option(
                            value=value,
                            text=text,
                            selected=selected,
                        )
                    )

                field.value = selected_value

                # Procurar label associado
                field.text = self.find_label(
                    soup,
                    select,
                )

                form.fields.append(field)

            # ------------------------------------------------
            # INPUT
            # ------------------------------------------------

            for inp in html_form.find_all("input"):

                input_type = (
                    inp.get("type")
                    or "text"
                ).lower()

                name = inp.get("name")

                field_id = inp.get("id")

                value = inp.get("value")

                field = Field(
                    field_type=input_type,
                    name=name,
                    field_id=field_id,
                    value=value,
                )

                field.text = self.find_label(
                    soup,
                    inp,
                )

                form.fields.append(field)

            forms.append(form)

        return Page(
            url=url,
            status=response.status_code,
            bytes=len(response.content),
            title=title,
            links=list(dict.fromkeys(links)),
            forms=forms,
        )

    # ========================================================
    # LABEL
    # ========================================================

    def find_label(self, soup, element):

        element_id = element.get("id")

        if element_id:

            label = soup.find(
                "label",
                attrs={"for": element_id},
            )

            if label:

                return label.get_text(
                    " ",
                    strip=True,
                )

        parent = element.parent

        if parent:

            text = parent.get_text(
                " ",
                strip=True,
            )

            if text:
                return text

        return ""

    # ========================================================
    # SALVAR HTML
    # ========================================================

    def save_raw(self, url, response):

        filename = self.safe_filename(url)

        path = self.raw_dir / (
            filename + ".html"
        )

        with path.open(
            "w",
            encoding="utf-8",
            errors="replace",
        ) as f:

            f.write(response.text)

    # ========================================================
    # CRAWL
    # ========================================================

    def crawl(self, start_path="/"):

        queue = deque()

        start_url = self.make_url(
            start_path
        )

        queue.append(start_url)

        while queue:

            if len(self.pages) >= self.max_pages:

                print(
                    "[!] Limite de páginas atingido."
                )

                break

            url = queue.popleft()

            if url in self.visited:
                continue

            self.visited.add(url)

            print(
                f"[{len(self.pages)+1:04d}] {url}"
            )

            response = self.fetch(url)

            if response is None:
                continue

            print(
                f"      HTTP {response.status_code}"
                f" - {len(response.content)} bytes"
            )

            self.save_raw(
                url,
                response,
            )

            # ------------------------------------------------
            # Só interpretar HTML
            # ------------------------------------------------

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                ).lower()
            )

            if (
                "text/html" not in content_type
                and not url.endswith(
                    (".html", ".htm")
                )
            ):

                continue

            page = self.parse_page(
                url,
                response,
            )

            self.pages.append(page)

            for link in page.links:

                if link not in self.visited:

                    queue.append(link)

            time.sleep(0.05)

        return self.pages

    # ========================================================
    # SALVAR RESULTADOS
    # ========================================================

    def save_results(self):

        pages_data = []

        for page in self.pages:

            pages_data.append({
                "url": page.url,
                "status": page.status,
                "bytes": page.bytes,
                "title": page.title,
                "links": page.links,

                "forms": [

                    {
                        "action": form.action,
                        "method": form.method,

                        "fields": [

                            {
                                "type": field.field_type,
                                "name": field.name,
                                "id": field.field_id,
                                "value": field.value,
                                "text": field.text,

                                "options": [

                                    {
                                        "value": option.value,
                                        "text": option.text,
                                        "selected": option.selected,
                                    }

                                    for option in field.options
                                ],
                            }

                            for field in form.fields
                        ],
                    }

                    for form in page.forms
                ],
            })

        map_path = (
            self.map_dir
            / f"ews_{self.printer_ip.replace('.', '_')}.json"
        )

        with map_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                pages_data,
                f,
                indent=2,
                ensure_ascii=False,
            )

        knowledge = build_knowledge(
            self.pages
        )

        knowledge_path = (
            self.knowledge_dir
            / f"knowledge_{self.printer_ip.replace('.', '_')}.json"
        )

        save_knowledge(
            knowledge,
            knowledge_path,
        )

        return map_path, knowledge_path