import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = input("URL inicial: ").strip()

visitados = set()
fila = [BASE]


while fila:

    url = fila.pop(0)

    if url in visitados:
        continue

    visitados.add(url)

    try:
        r = requests.get(url, timeout=5)
    except:
        continue

    print("=" * 70)
    print(url)
    print(r.status_code)

    if "text/html" not in r.headers.get("Content-Type", ""):
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    print()

    # LINKS

    for a in soup.find_all("a", href=True):

        link = urljoin(url, a["href"])

        print("LINK :", link)

        if (
            link.startswith("http://192.168.")
            and link not in visitados
        ):
            fila.append(link)

    # FORMS

    for form in soup.find_all("form"):

        action = form.get("action")

        method = form.get("method")

        print()
        print("FORM")
        print(" ACTION:", action)
        print(" METHOD:", method)

        for inp in form.find_all("input"):

            print(
                "   INPUT",
                inp.get("type"),
                inp.get("name"),
                inp.get("value")
            )

        for sel in form.find_all("select"):

            print(
                "   SELECT",
                sel.get("name")
            )

    # SCRIPTS

    for s in soup.find_all("script"):

        if s.get("src"):

            print("SCRIPT:", s["src"])