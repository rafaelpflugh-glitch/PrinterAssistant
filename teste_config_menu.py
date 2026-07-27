import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"


url=f"http://{ip}/cgi-bin/dynamic/config/config.html"


r=requests.get(
    url,
    timeout=20
)


print("STATUS:",r.status_code)



soup=BeautifulSoup(
    r.text,
    "html.parser"
)


for a in soup.find_all("a"):

    print(
        a.text.strip(),
        "=>",
        a.get("href")
    )



with open(
    "data/config_menu.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(r.text)