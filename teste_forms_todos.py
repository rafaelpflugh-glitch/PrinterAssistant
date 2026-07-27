import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ip = "192.168.14.134"

paginas = [
    "/",
    "/cgi-bin/dynamic/config/config.html",
    "/cgi-bin/dynamic/reports_and_information.html",
    "/cgi-bin/dynamic/printer/config/remote_oppanel.html",
    "/cgi-bin/dynamic/printer/config/remote_oppanel_config.html",
]

for pagina in paginas:

    print("\n" + "="*80)
    print(pagina)
    print("="*80)

    try:
        html = requests.get(f"http://{ip}{pagina}", timeout=10).text
    except Exception as e:
        print(e)
        continue

    soup = BeautifulSoup(html, "html.parser")

    forms = soup.find_all("form")

    if not forms:
        print("Nenhum formulário.")
        continue

    for form in forms:

        print("\nACTION:", form.get("action"))
        print("METHOD:", form.get("method"))

        for tag in form.find_all(["input","button","select"]):
            print(tag)