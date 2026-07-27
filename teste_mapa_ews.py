import os
import re

import requests

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


IP = "192.168.14.134"

BASE = f"http://{IP}"

PASTA = "ews_dump"


os.makedirs(
    PASTA,
    exist_ok=True
)


visitados = set()



def nome_arquivo(url):

    p = urlparse(url)

    nome = p.path.replace("/", "_")

    if p.query:

        nome += "_" + p.query


    nome = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        nome
    )


    nome = nome.strip("_")


    if not nome:

        nome = "index"


    return nome + ".html"




def salvar(url, html):

    arquivo = nome_arquivo(url)


    caminho = os.path.join(
        PASTA,
        arquivo
    )


    with open(
        caminho,
        "w",
        encoding="utf8",
        errors="ignore"
    ) as f:

        f.write(html)




def extrair_links(html, url):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    links = []


    # links normais

    for tag in soup.find_all(
        "a",
        href=True
    ):

        links.append(
            tag["href"]
        )


    # frames

    for tag in soup.find_all(
        [
            "frame",
            "iframe"
        ],
        src=True
    ):

        links.append(
            tag["src"]
        )


    # scripts simples

    encontrados = re.findall(
        r'["\'](\/cgi-bin\/[^"\']+)',
        html
    )


    links.extend(
        encontrados
    )


    urls = []


    for link in links:

        novo = urljoin(
            url,
            link
        )


        if novo.startswith(BASE):

            urls.append(
                novo
            )


    return urls




def baixar(url):


    if url in visitados:

        return



    visitados.add(url)


    print(url)


    try:

        r = requests.get(
            url,
            timeout=10
        )


    except Exception:

        return



    if "text/html" not in r.headers.get(
        "Content-Type",
        ""
    ):

        return



    html = r.text


    salvar(
        url,
        html
    )



    for link in extrair_links(
        html,
        url
    ):

        baixar(
            link
        )




print("="*40)

print("MAPEANDO EWS LEXMARK")

print("="*40)



baixar(
    BASE
)



print()

print("="*40)

print(
    "TOTAL DE PAGINAS:",
    len(visitados)
)

print("="*40)	