import requests
import re

ip = "192.168.14.134"

paginas = [
    "/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
    "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",
    "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",
    "/cgi-bin/dynamic/reports_and_information.html",
    "/cgi-bin/dynamic/config/config.html",
]

palavras = [
    "post",
    "cgi-bin",
    "script",
    "action",
    "submit",
    "print",
    "device",
    "report",
    "onclick",
    "javascript",
]

for pagina in paginas:

    print("\n==============================")
    print(pagina)

    html = requests.get(f"http://{ip}{pagina}").text

    for p in palavras:

        if p.lower() in html.lower():

            print("Encontrou:", p)