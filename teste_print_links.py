import requests
from bs4 import BeautifulSoup

ip = "192.168.14.134"

urls = [
    "/cgi-bin/dynamic/printer/config/reports/MenusPage.html",
    "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",
    "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",
]

for u in urls:

    url = "http://" + ip + u

    print("\n====================")
    print(url)

    r = requests.get(url)

    print("STATUS:", r.status_code)

    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )

    for form in soup.find_all("form"):

        print("\nFORM:")
        print(form)

    for a in soup.find_all("a"):

        href = a.get("href")

        if href:

            print("LINK:", href)