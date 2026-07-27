import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"


url=(
    f"http://{ip}"
    "/cgi-bin/dynamic/printer/config/remote_oppanel.html"
)


print("==============================")
print("PAINEL REMOTO")
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
    "data/remote_oppanel.html",
    "w",
    encoding="utf-8"
).write(
    r.text
)


print(
    "TAMANHO:",
    len(r.text)
)


soup=BeautifulSoup(
    r.text,
    "html.parser"
)


print()
print("==============================")
print("FORMS")
print("==============================")


for form in soup.find_all("form"):

    print(
        "ACTION:",
        form.get("action")
    )

    print(
        "METHOD:",
        form.get("method")
    )


print()
print("==============================")
print("INPUTS")
print("==============================")


for inp in soup.find_all("input"):

    print(
        inp.get("name"),
        "=",
        inp.get("value"),
        inp.get("type")
    )


print()
print("==============================")
print("CGI/JAVASCRIPT")
print("==============================")


for linha in r.text.splitlines():

    if (
        "cgi" in linha.lower()
        or
        "button" in linha.lower()
        or
        "key" in linha.lower()
        or
        "ajax" in linha.lower()
    ):

        print(linha)