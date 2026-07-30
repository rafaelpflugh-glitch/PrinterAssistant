import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class EWSCrawler:

    def __init__(self, ip):

        self.ip = ip
        self.base = f"http://{ip}"

        self.visitados = set()
        self.encontrados = []

    def explorar(self):

        sementes = [

            "/",

            "/cgi-bin/dynamic/printer/PrinterStatus.html",

            "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",

            "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",

            "/cgi-bin/dynamic/linksindex.html"

        ]

        for pagina in sementes:
            self.visitar(pagina)

        return sorted(self.encontrados)

    def visitar(self, caminho):

        if caminho in self.visitados:
            return

        self.visitados.add(caminho)

        url = urljoin(self.base, caminho)

        try:

            resposta = requests.get(
                url,
                timeout=5
            )

        except Exception:
            return

        if resposta.status_code != 200:
            return

        print(caminho)

        self.encontrados.append(caminho)

        soup = BeautifulSoup(
            resposta.text,
            "html.parser"
        )

        # Procura links normais
        for tag in soup.find_all(["a", "frame", "iframe"]):

            href = tag.get("href") or tag.get("src")

            if not href:
                continue

            if href.startswith("javascript"):
                continue

            if href.startswith("mailto"):
                continue

            href = href.split("#")[0]
            href = href.split("?")[0]

            href = urljoin("/", href)

            if href.startswith("/cgi-bin"):
                self.visitar(href)