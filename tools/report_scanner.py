import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scan_report(url):

    print("="*60)
    print("SCANEANDO RELATORIO")
    print("="*60)
    print(url)


    try:

        r = requests.get(
            url,
            timeout=30
        )

    except Exception as e:

        print("ERRO:",e)
        return



    print()
    print("STATUS:",r.status_code)

    html = r.text


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    print()
    print("="*60)
    print("FORMS")
    print("="*60)


    for form in soup.find_all("form"):

        print()

        print(
            "ACTION:",
            urljoin(
                url,
                form.get("action","")
            )
        )

        print(
            "METHOD:",
            form.get(
                "method",
                "GET"
            )
        )


        for item in form.find_all(
            [
                "input",
                "button",
                "select"
            ]
        ):

            print(
                "CAMPO:",
                item.name,
                item.attrs
            )



    print()
    print("="*60)
    print("LINKS")
    print("="*60)


    for a in soup.find_all(
        "a",
        href=True
    ):

        texto=a.text.strip()

        if texto:

            print(
                texto,
                "->",
                urljoin(
                    url,
                    a["href"]
                )
            )


    print()
    print("="*60)
    print("BOTOES")
    print("="*60)


    for b in soup.find_all(
        ["input","button"]
    ):

        print(
            b.attrs
        )


    print()
    print("="*60)
    print("PALAVRAS CHAVE")
    print("="*60)


    palavras=[
        "demo",
        "print",
        "page",
        "report",
        "teste",
        "impress"
    ]


    for p in palavras:

        if p.lower() in html.lower():

            print(
                "ENCONTRADO:",
                p
            )



if __name__=="__main__":

    url=input(
        "URL:"
    )

    scan_report(url)