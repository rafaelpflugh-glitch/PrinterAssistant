import requests
from bs4 import BeautifulSoup


ip = "192.168.14.134"


paginas = [
    "/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
    "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",
    "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html"
]


for pagina in paginas:

    url = "http://" + ip + pagina

    print("\n====================")
    print(url)


    r = requests.get(url)


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    print("\nFORMS:")


    for form in soup.find_all("form"):

        print("----------------")
        print("ACTION:", form.get("action"))
        print("METHOD:", form.get("method"))


        for inp in form.find_all("input"):

            print(
                "INPUT:",
                inp.get("name"),
                "=",
                inp.get("value")
            )