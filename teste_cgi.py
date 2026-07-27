import requests
from bs4 import BeautifulSoup

ip = "192.168.14.134"

paginas = [
    "/",
    "/cgi-bin/dynamic/reports_and_information.html",
    "/cgi-bin/dynamic/config/config.html",
    "/cgi-bin/dynamic/printer/PrinterStatus.html",
    "/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
]

for pagina in paginas:

    print("\n", "=" * 70)
    print(pagina)

    html = requests.get(f"http://{ip}{pagina}").text

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(True):

        for valor in tag.attrs.values():

            texto = str(valor)

            if "/cgi-bin/" in texto:

                print(texto)