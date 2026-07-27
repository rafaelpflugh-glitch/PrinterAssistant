import requests

ip="192.168.14.134"

paginas=[
"/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
"/cgi-bin/dynamic/reports_and_information.html",
"/cgi-bin/dynamic/printer/PrinterStatus.html"
]


for p in paginas:

    print("\n==============")
    print(p)

    r=requests.get(
        "http://"+ip+p
    )

    texto=r.text.lower()

    for linha in texto.splitlines():

        if "print" in linha or "submit" in linha or "form" in linha:

            print(linha)