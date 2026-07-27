from bs4 import BeautifulSoup


arquivo = "data/deviceinfo.html"


with open(
    arquivo,
    encoding="utf-8"
) as f:

    html = f.read()



soup = BeautifulSoup(
    html,
    "html.parser"
)



print()
print("==============================")
print("LINKS")
print("==============================")



for link in soup.find_all("a"):

    print(
        "TEXT:",
        link.text.strip(),
        "HREF:",
        link.get("href")
    )



print()
print("==============================")
print("SCRIPTS")
print("==============================")



for script in soup.find_all("script"):


    if script.get("src"):

        print(
            "SRC:",
            script.get("src")
        )

    else:

        texto = script.text.strip()

        if texto:

            print()

            print(texto[:500])