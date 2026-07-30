import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extrair_menu(url):

    print("=" * 60)
    print("MAPEANDO MENU LEXMARK")
    print("=" * 60)
    print(url)


    r = requests.get(
        url,
        timeout=10
    )


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    print()
    print("=" * 60)
    print("LINKS")
    print("=" * 60)


    for tag in soup.find_all(
        ["a","form","input","area"]
    ):

        print()


        print(
            "TAG:",
            tag.name
        )


        if tag.get("href"):

            print(
                "HREF:",
                urljoin(
                    url,
                    tag["href"]
                )
            )


        if tag.get("action"):

            print(
                "ACTION:",
                urljoin(
                    url,
                    tag["action"]
                )
            )


        if tag.get("onclick"):

            print(
                "ONCLICK:",
                tag["onclick"]
            )


        if tag.get("name"):

            print(
                "NAME:",
                tag["name"]
            )


        if tag.get("value"):

            print(
                "VALUE:",
                tag["value"]
            )



    print()
    print("=" * 60)
    print("TEXTOS DO MENU")
    print("=" * 60)


    for texto in soup.stripped_strings:

        print(
            texto
        )



if __name__ == "__main__":

    url=input(
        "URL MENU: "
    )

    extrair_menu(url)