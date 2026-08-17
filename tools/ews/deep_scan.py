import sys
import os
import json
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class EWSParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.links = []
        self.forms = []

        self.form = None
        self.select = None
        self.option = None

    def handle_starttag(self, tag, attrs):

        attrs = dict(attrs)

        if tag in ("a", "link"):
            target = attrs.get("href")

            if target:
                self.links.append(target)

        elif tag in ("script", "frame", "iframe"):
            target = attrs.get("src")

            if target:
                self.links.append(target)

        elif tag == "form":

            self.form = {
                "action": attrs.get("action"),
                "method": attrs.get("method", "GET").upper(),
                "fields": []
            }

        elif tag == "select" and self.form is not None:

            self.select = {
                "name": attrs.get("name"),
                "id": attrs.get("id"),
                "options": []
            }

        elif tag == "option" and self.select is not None:

            self.option = {
                "value": attrs.get("value"),
                "selected": "selected" in attrs,
                "text": ""
            }

        elif tag == "input" and self.form is not None:

            self.form["fields"].append({
                "type": attrs.get("type", "text"),
                "name": attrs.get("name"),
                "value": attrs.get("value")
            })

    def handle_data(self, data):

        if self.option is not None:
            self.option["text"] += data.strip()

    def handle_endtag(self, tag):

        if tag == "option":

            if self.select is not None and self.option is not None:
                self.select["options"].append(self.option)

            self.option = None

        elif tag == "select":

            if self.form is not None and self.select is not None:

                self.form["fields"].append({
                    "type": "select",
                    "name": self.select["name"],
                    "id": self.select["id"],
                    "options": self.select["options"]
                })

            self.select = None

        elif tag == "form":

            if self.form is not None:
                self.forms.append(self.form)

            self.form = None


def fetch(url):

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PrinterAssistant/1.0",
            "Accept": "text/html,*/*"
        }
    )

    with urllib.request.urlopen(req, timeout=10) as r:

        data = r.read()

        return r.status, data.decode(
            "utf-8",
            errors="replace"
        )


def absolute(base, target):

    if not target:
        return None

    if target.startswith("#"):
        return None

    return urljoin(base, target)


def scan(ip, start):

    base = "http://" + ip

    first = absolute(base, start)

    queue = [first]
    visited = set()

    pages = []

    while queue:

        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        print()
        print("=" * 70)
        print(f"[{len(visited):04}] {url}")
        print("=" * 70)

        try:

            status, html = fetch(url)

        except Exception as e:

            print("[ERRO]", e)
            continue

        parser = EWSParser()

        try:
            parser.feed(html)

        except Exception as e:

            print("[ERRO PARSER]", e)

        print("HTTP :", status)
        print("BYTES:", len(html))
        print("FORMS:", len(parser.forms))
        print("LINKS:", len(parser.links))

        page = {
            "url": url,
            "status": status,
            "bytes": len(html),
            "forms": parser.forms,
            "links": parser.links
        }

        pages.append(page)

        # Mostrar formulários encontrados

        for n, form in enumerate(parser.forms, 1):

            print()
            print(f"FORM #{n}")
            print("ACTION:", form["action"])
            print("METHOD:", form["method"])

            for field in form["fields"]:

                if field["type"] == "select":

                    print()
                    print(" SELECT:", field["name"])

                    for option in field["options"]:

                        marker = " [ATUAL]" if option["selected"] else ""

                        print(
                            f"    {option['value']} = "
                            f"{option['text']}{marker}"
                        )

                else:

                    print(
                        " INPUT:",
                        field["type"],
                        field["name"],
                        "=",
                        field["value"]
                    )

        # Descobrir novos links

        for link in parser.links:

            target = absolute(url, link)

            if not target:
                continue

            a = urlparse(target)
            b = urlparse(base)

            if a.netloc != b.netloc:
                continue

            if target not in visited:
                queue.append(target)

    return pages


def main():

    if len(sys.argv) < 2:

        print()
        print(
            "Uso: python tools\\ews\\deep_scan.py "
            "IP [CAMINHO]"
        )
        sys.exit(1)

    ip = sys.argv[1]

    start = "/"

    if len(sys.argv) >= 3:
        start = sys.argv[2]

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT")
    print("EWS DEEP SCANNER")
    print("=" * 70)
    print()
    print("Impressora:", ip)
    print("Início    :", start)

    pages = scan(ip, start)

    os.makedirs("ews/dump", exist_ok=True)

    filename = (
        "ews/dump/deep_"
        + ip.replace(".", "_")
        + ".json"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pages,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("SCAN FINALIZADO")
    print("=" * 70)
    print()
    print("Páginas:", len(pages))
    print("Mapa   :", filename)
    print()


if __name__ == "__main__":
    main()