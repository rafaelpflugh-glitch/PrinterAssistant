import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def mapear(ip):

    base = f"http://{ip}"

    paginas = [
        "/",
        "/cgi-bin/dynamic/left_bar.html",
        "/cgi-bin/dynamic/topbar.html",
        "/cgi-bin/dynamic/se_index.html"
    ]

    encontrados = set()

    with requests.Session() as sessao:

        sessao.headers.update({
            "User-Agent": "PrinterAssistant/1.0",
            "Connection": "close"
        })

        for pagina in paginas:

            url = base + pagina

            try:

                print(f"\nANALISANDO: {url}")

                resposta = sessao.get(
                    url,
                    timeout=5
                )

                resposta.close()

                soup = BeautifulSoup(
                    resposta.text,
                    "html.parser"
                )

                for tag in soup.find_all(
                    ["a", "form", "frame", "iframe"]
                ):

                    for atributo in (
                        "href",
                        "src",
                        "action"
                    ):

                        valor = tag.get(atributo)

                        if not valor:
                            continue

                        completo = urljoin(
                            url,
                            valor
                        )

                        if completo not in encontrados:

                            encontrados.add(completo)
                            print(completo)

            except Exception as erro:

                print("ERRO:", erro)

    print("\n======================")
    print("TOTAL:", len(encontrados))

    return sorted(encontrados)


if __name__ == "__main__":

    mapear("192.168.14.134")