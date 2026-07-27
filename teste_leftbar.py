import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"


url=f"http://{ip}/cgi-bin/dynamic/left_bar.html"


r=requests.get(
    url,
    timeout=10
)


print("==============================")
print("STATUS")
print("==============================")

print(r.status_code)



with open(
    "data/left_bar.html",
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


print()
print("SALVO data/left_bar.html")