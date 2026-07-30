import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque

class EWSExplorer:

    def __init__(self, ip):

        self.base = f"http://{ip}"
        self.visitados = set()

    def explorar(self, inicio="/"):

        fila = deque([inicio])

        while fila:

            pagina = fila.popleft()

            if pagina in self.visitados:
                continue

            self.visitados.add(pagina)

            url = urljoin(self.base, pagina)

            try:

                r = requests.get(
                    url,
                    timeout=8
                )

            except Exception:
                continue

            print("\n"+"="*80)
            print(r.status_code, pagina)
            print("="*80)

            print("Content-Type:", r.headers.get("Content-Type"))
            print("Content-Length:", len(r.text))

            soup = BeautifulSoup(r.text, "html.parser")

            #
            # LINKS
            #

            for a in soup.find_all("a"):

                href = a.get("href")

                if not href:
                    continue

                print("LINK :", href)

                if href.startswith("/"):

                    if href not in self.visitados:

                        fila.append(href)

            #
            # FORMULÁRIOS
            #

            for form in soup.find_all("form"):

                print("\nFORM")

                print("ACTION :", form.get("action"))
                print("METHOD :", form.get("method"))

                for campo in form.find_all(["input","button","select"]):

                    print(campo)

            #
            # JAVASCRIPT
            #

            for script in soup.find_all("script"):

                if script.get("src"):

                    print("SCRIPT :", script["src"])

                    if script["src"].startswith("/"):

                        fila.append(script["src"])

            #
            # FRAMES
            #

            for frame in soup.find_all(["frame","iframe"]):

                src = frame.get("src")

                if src:

                    print("FRAME :", src)

                    if src.startswith("/"):

                        fila.append(src)