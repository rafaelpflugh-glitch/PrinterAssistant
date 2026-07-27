import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings()

IP = "192.168.14.134"

BASE = f"http://{IP}"

visitados = set()


def explorar(url, nivel=0):

    if url in visitados:
        return

    visitados.add(url)

    try:

        r = requests.get(
            url,
            timeout=5,
            verify=False
        )

        print(
            " " * nivel,
            f"[{r.status_code}] {url}"
        )

        if "text/html" not in r.headers.get(
            "Content-Type",
            ""
        ):
            return

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        # Links
        for a in soup.find_all("a", href=True):

            novo = urljoin(
                url,
                a["href"]
            )

            if BASE in novo:
                explorar(
                    novo,
                    nivel + 2
                )

        # Forms
        for form in soup.find_all("form"):

            action = form.get(
                "action",
                ""
            )

            metodo = form.get(
                "method",
                "GET"
            ).upper()

            destino = urljoin(
                url,
                action
            )

            print(
                " " * (nivel + 2),
                f"FORM {metodo} -> {destino}"
            )

    except Exception as e:

        print(
            " " * nivel,
            "ERRO:",
            url,
            e
        )


explorar(BASE)

print()
print("=" * 50)
print("TOTAL DE PÁGINAS:", len(visitados))