import sys
import os
import re
import json
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class EWSParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.forms = []
        self.current_form = None
        self.current_select = None
        self.current_option = None
        self.current_input = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "a":
            href = attrs.get("href")
            if href:
                self.links.append(href)

        elif tag == "form":
            self.current_form = {
                "action": attrs.get("action"),
                "method": attrs.get("method", "GET").upper(),
                "fields": []
            }

        elif tag == "select" and self.current_form is not None:
            self.current_select = {
                "name": attrs.get("name"),
                "id": attrs.get("id"),
                "options": []
            }

        elif tag == "option" and self.current_select is not None:
            self.current_option = {
                "value": attrs.get("value"),
                "selected": "selected" in attrs,
                "text": ""
            }

        elif tag == "input" and self.current_form is not None:
            self.current_form["fields"].append({
                "type": attrs.get("type", "text"),
                "name": attrs.get("name"),
                "value": attrs.get("value"),
            })

    def handle_data(self, data):
        if self.current_option is not None:
            self.current_option["text"] += data.strip()

    def handle_endtag(self, tag):
        if tag == "option":
            if self.current_select is not None and self.current_option is not None:
                self.current_select["options"].append(self.current_option)
            self.current_option = None

        elif tag == "select":
            if self.current_form is not None and self.current_select is not None:
                self.current_form["fields"].append({
                    "type": "select",
                    "name": self.current_select["name"],
                    "id": self.current_select["id"],
                    "options": self.current_select["options"]
                })

            self.current_select = None

        elif tag == "form":
            if self.current_form is not None:
                self.forms.append(self.current_form)

            self.current_form = None


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PrinterAssistant/1.0",
            "Accept": "text/html,application/xhtml+xml"
        }
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, response.read().decode(
            "utf-8",
            errors="replace"
        )


def normalize_url(base, target):
    if not target:
        return None

    if target.startswith("#"):
        return None

    return urljoin(base, target)


def crawl(base_url, start_path="/"):
    start_url = normalize_url(base_url, start_path)

    visited = set()
    queue = [start_url]
    discovered = []

    while queue:
        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        print(f"[{len(visited):03}] {url}")

        try:
            status, html = fetch(url)
        except Exception as e:
            print(f"      [ERRO] {e}")
            continue

        print(f"      HTTP {status} - {len(html)} bytes")

        parser = EWSParser()

        try:
            parser.feed(html)
        except Exception as e:
            print(f"      [WARN] Parser: {e}")

        item = {
            "url": url,
            "status": status,
            "size": len(html),
            "forms": parser.forms,
            "links": parser.links,
        }

        discovered.append(item)

        # Descobrir links internos
        for link in parser.links:
            absolute = normalize_url(url, link)

            if not absolute:
                continue

            parsed_base = urlparse(base_url)
            parsed_link = urlparse(absolute)

            if parsed_link.netloc != parsed_base.netloc:
                continue

            if absolute not in visited:
                queue.append(absolute)

    return discovered


def save_results(results, ip):
    os.makedirs("ews", exist_ok=True)
    os.makedirs("ews/dump", exist_ok=True)

    filename = f"ews/dump/crawl_{ip.replace('.', '_')}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    return filename


def main():
    if len(sys.argv) < 2:
        print()
        print("Uso:")
        print()
        print("  python tools\\ews_crawl.py 192.168.14.134 /")
        print()
        sys.exit(1)

    ip = sys.argv[1]

    start_path = "/"

    if len(sys.argv) >= 3:
        start_path = sys.argv[2]

    base_url = f"http://{ip}"

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT")
    print("EWS CRAWLER")
    print("=" * 70)
    print()
    print(f"Impressora : {ip}")
    print(f"Início     : {start_path}")
    print()
    print("Iniciando descoberta...")
    print()

    results = crawl(base_url, start_path)

    filename = save_results(results, ip)

    print()
    print("=" * 70)
    print("CRAWL FINALIZADO")
    print("=" * 70)
    print()
    print(f"Páginas descobertas: {len(results)}")
    print(f"Mapa salvo em      : {filename}")
    print()


if __name__ == "__main__":
    main()