import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"


url=(
    f"http://{ip}"
    "/cgi-bin/dynamic/printer/config/gen/printersettings.html"
)


print("==============================")
print("ANALISANDO")
print(url)
print("==============================")


r=requests.get(
    url,
    timeout=30
)


print(
    "STATUS:",
    r.status_code
)


open(
    "data/printersettings.html",
    "w",
    encoding="utf-8"
).write(
    r.text
)


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


print()
print("==============================")
print("FORMS")
print("==============================")


for f in soup.find_all("form"):

    print(
        "ACTION:",
        f.get("action"),
        "METHOD:",
        f.get("method")
    )


print()
print("==============================")
print("TEXTOS CGI")
print("==============================")


for linha in r.text.splitlines():

    if "cgi" in linha.lower():

        print(linha)