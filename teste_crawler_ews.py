import requests
from bs4 import BeautifulSoup


ip = "192.168.14.134"

url = f"http://{ip}"


print("==============================")
print("LEXMARK EWS CRAWLER")
print("==============================")



r = requests.get(
    url,
    timeout=10
)



print(
    "Status:",
    r.status_code
)



print("\nTamanho HTML:",
      len(r.text)
)



print("\nPALAVRAS IMPORTANTES:\n")



palavras = [

    "print",
    "report",
    "configuration",
    "reset",
    "scanner",
    "usb",
    "paper",
    "media",
    "demo",
    "asset",
    "status"

]


html = r.text.lower()


for p in palavras:

    if p in html:

        print(
            "Encontrado:",
            p
        )



soup = BeautifulSoup(
    r.text,
    "html.parser"
)



print("\nFORMS ENCONTRADOS\n")



for form in soup.find_all("form"):

    print("----------------")

    print(
        "ACTION:",
        form.get("action")
    )

    print(
        "METHOD:",
        form.get("method")
    )


    for inp in form.find_all("input"):

        print(
            "INPUT:",
            inp.get("name"),
            "=",
            inp.get("value")
        )



print("\nSCRIPTS\n")



for script in soup.find_all("script"):

    src = script.get("src")

    if src:

        print(src)



print("\nFRAMES\n")



for frame in soup.find_all(
    ["frame","iframe"]
):

    print(
        frame.get("src")
    )



print("\nFIM")