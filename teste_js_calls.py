import requests
import re

ip="192.168.14.134"

paginas=[

"/cgi-bin/dynamic/reports_and_information.html",

"/cgi-bin/dynamic/config/config.html",

"/cgi-bin/dynamic/left_bar.html",

"/cgi-bin/dynamic/topbar.html",

"/cgi-bin/dynamic/printer/PrinterStatus.html"

]

padrao=re.compile(
r'window\.location|location\.href|submit|action=|print|cgi-bin/direct|cgi-bin/script',
re.I
)

for p in paginas:

    print("="*70)
    print(p)

    html=requests.get(f"http://{ip}{p}",timeout=5).text

    for linha in html.splitlines():

        if padrao.search(linha):

            print(linha.strip())