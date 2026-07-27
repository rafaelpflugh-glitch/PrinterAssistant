import requests
from bs4 import BeautifulSoup

ip = "192.168.14.134"

paginas = [

"/cgi-bin/dynamic/printer/config/gen/papermenu.html",
"/cgi-bin/dynamic/printer/config/gen/printersettings.html",
"/cgi-bin/dynamic/printer/config/gen/general.html",
"/cgi-bin/dynamic/printer/config/gen/copy.html"

]

for pagina in paginas:

    print("\n")
    print("="*70)
    print(pagina)

    html = requests.get(f"http://{ip}{pagina}").text

    soup = BeautifulSoup(html,"html.parser")

    for form in soup.find_all("form"):

        print("\nFORM")

        print("ACTION :",form.get("action"))

        print("METHOD :",form.get("method"))

        print()

        for campo in form.find_all(["input","select","button"]):

            print(campo)