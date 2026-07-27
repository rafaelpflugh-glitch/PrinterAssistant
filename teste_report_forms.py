import requests
from bs4 import BeautifulSoup


ip = "192.168.14.134"

url = (
    f"http://{ip}"
    "/cgi-bin/dynamic/printer/config/reports/printdirectory.html"
)


print("==============================")
print("ANALISANDO")
print(url)
print("==============================")


r = requests.get(
    url,
    timeout=30
)


print(
    "STATUS:",
    r.status_code
)


soup = BeautifulSoup(
    r.text,
    "html.parser"
)


print()
print("==============================")
print("FORMS")
print("==============================")


for form in soup.find_all("form"):

    print()

    print(
        "ACTION:",
        form.get("action")
    )

    print(
        "METHOD:",
        form.get("method")
    )


    for inp in form.find_all(
        ["input","button"]
    ):

        print(
            inp.name,
            inp.get("type"),
            inp.get("name"),
            inp.get("value"),
            inp.text.strip()
        )