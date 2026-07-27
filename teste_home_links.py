import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"

url=f"http://{ip}"


r=requests.get(url)


soup=BeautifulSoup(
    r.text,
    "html.parser"
)



print("==============================")
print("LINKS HOME")
print("==============================")


for a in soup.find_all("a"):

    print(

        a.text.strip(),

        "=>",

        a.get("href")

    )