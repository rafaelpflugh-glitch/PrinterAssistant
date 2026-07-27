import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"


url=f"http://{ip}/cgi-bin/dynamic/reports_and_information.html"


r=requests.get(
    url,
    timeout=30
)


print("STATUS:",r.status_code)


soup=BeautifulSoup(
    r.text,
    "html.parser"
)


print()
print("==============================")
print("LINKS")
print("==============================")


for a in soup.find_all("a"):

    print(
        a.text.strip(),
        "=>",
        a.get("href")
    )


open(
    "data/reports_root.html",
    "w",
    encoding="utf-8"
).write(r.text)