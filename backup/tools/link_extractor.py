import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extrair_links(url):

    print("=" * 60)
    print("EXTRAINDO LINKS")
    print("=" * 60)
    print(url)


    try:

        r = requests.get(
            url,
            timeout=10
        )

    except Exception as e:

        print("ERRO:", e)
        return []


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    links = []


    for a in soup.find_all(
        "a",
        href=True
    ):

        href = urljoin(
            url,
            a["href"]
        )

        texto = a.text.strip()


        links.append(
            {
                "texto": texto,
                "url": href
            }
        )


    return links



if __name__ == "__main__":


    url = input(
        "URL da impressora: "
    )


    links = extrair_links(
        url
    )


    print()

    print("=" * 60)

    print(
        "LINKS ENCONTRADOS:",
        len(links)
    )

    print("=" * 60)



    for l in links:

        print()

        print(
            "[",
            l["texto"],
            "]"
        )

        print(
            l["url"]
        )