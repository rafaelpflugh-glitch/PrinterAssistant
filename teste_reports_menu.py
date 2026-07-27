import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"

url=f"http://{ip}/cgi-bin/dynamic/reports_and_information.html"


r=requests.get(url)


print("STATUS:", r.status_code)


with open(
    "data/reports_menu.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(r.text)


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