import requests
from bs4 import BeautifulSoup
import time


def analisar(url):

    print("=" * 60)
    print("ANALISANDO PAGINA")
    print("=" * 60)
    print(url)

    try:

        inicio = time.time()

        r = requests.get(
            url,
            timeout=30
        )

        tempo = time.time() - inicio

    except Exception as e:

        print("ERRO:", e)
        return

    print()
    print("TEMPO RESPOSTA:")
    print(round(tempo, 2), "segundos")

    print()
    print("STATUS:")
    print(r.status_code)

    print()
    print("HEADERS")
    print("=" * 60)

    for k, v in r.headers.items():
        print(f"{k}: {v}")

    html = r.text

    with open(
        "dump_page.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    print()
    print("HTML salvo em dump_page.html")

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # =====================================================

    print()
    print("=" * 60)
    print("LINKS")
    print("=" * 60)

    for a in soup.find_all("a"):

        txt = a.get_text(
            " ",
            strip=True
        )

        href = a.get("href")

        print(
            txt,
            "->",
            href
        )

    # =====================================================

    print()
    print("=" * 60)
    print("FORMS")
    print("=" * 60)

    for form in soup.find_all("form"):

        print("ACTION:", form.get("action"))
        print("METHOD:", form.get("method"))
        print()

    # =====================================================

    print()
    print("=" * 60)
    print("INPUTS")
    print("=" * 60)

    for inp in soup.find_all("input"):

        print(
            "TYPE:",
            inp.get("type"),
            "NAME:",
            inp.get("name"),
            "VALUE:",
            inp.get("value")
        )

        if inp.has_attr("checked"):
            print("   CHECKED")

        if inp.has_attr("disabled"):
            print("   DISABLED")

        if inp.has_attr("readonly"):
            print("   READONLY")

        if inp.get("onclick"):
            print("   onclick =", inp.get("onclick"))

    # =====================================================

    print()
    print("=" * 60)
    print("TEXTAREAS")
    print("=" * 60)

    for t in soup.find_all("textarea"):

        print("NAME:", t.get("name"))
        print(t.text.strip())
        print()

    # =====================================================

    print()
    print("=" * 60)
    print("SELECTS")
    print("=" * 60)

    for sel in soup.find_all("select"):

        print("SELECT:", sel.get("name"))

        for op in sel.find_all("option"):

            marca = ""

            if op.has_attr("selected"):
                marca = "   <== SELECIONADO"

            print(
                "   ",
                op.get("value"),
                "=",
                op.text.strip(),
                marca
            )

        print()

    # =====================================================

    print()
    print("=" * 60)
    print("BUTTONS")
    print("=" * 60)

    for b in soup.find_all(["button"]):

        print("TEXT :", b.text.strip())
        print("ATTR :", b.attrs)
        print()

    # =====================================================

    print()
    print("=" * 60)
    print("SCRIPTS")
    print("=" * 60)

    for s in soup.find_all("script"):

        src = s.get("src")

        if src:
            print("SRC :", src)
        else:

            txt = s.text.strip()

            if txt:

                print(txt[:400])
                print("...")

    # =====================================================

    print()
    print("=" * 60)
    print("META")
    print("=" * 60)

    for m in soup.find_all("meta"):

        print(m.attrs)

    # =====================================================

    print()
    print("=" * 60)
    print("TITULO")
    print("=" * 60)

    if soup.title:
        print(soup.title.text.strip())

    # =====================================================

    print()
    print("=" * 60)
    print("COMENTARIOS HTML")
    print("=" * 60)

    from bs4 import Comment

    for c in soup.find_all(
        string=lambda text: isinstance(text, Comment)
    ):

        print(c.strip())


if __name__ == "__main__":

    url = input("URL:")

    analisar(url)