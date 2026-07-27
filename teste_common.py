import requests


ip="192.168.14.134"

base=f"http://{ip}"

arquivos=[

"/index.html",

"/cgi-bin/dynamic/printer/index.html",

"/cgi-bin/dynamic/printer/menu.html",

"/cgi-bin/dynamic/printer/main.html",

"/cgi-bin/dynamic/printer/home.html",

"/cgi-bin/dynamic/printer/navigation.html"

]


for arq in arquivos:

    url=base+arq

    r=requests.get(
        url,
        timeout=5
    )


    print(
        r.status_code,
        arq
    )