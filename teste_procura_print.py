import requests
import re

ip = "192.168.14.134"

paginas = [
    "/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
    "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",
    "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",
    "/cgi-bin/dynamic/config/gen/setuppg.html"
]

palavras = [
    "print",
    "Print",
    "submit",
    "postpf",
    "onclick",
    "javascript",
    "cgi-bin/script",
    "button",
    "input",
    "action"
]

for pagina in paginas:

    print("="*70)
    print(pagina)

    html = requests.get(f"http://{ip}{pagina}").text

    for palavra in palavras:

        if palavra in html:

            print("Encontrou:", palavra)

            for linha in html.splitlines():

                if palavra.lower() in linha.lower():

                    print(linha)