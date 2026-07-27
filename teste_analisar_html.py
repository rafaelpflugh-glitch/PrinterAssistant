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
print("FORMS ENCONTRADOS")
print("==============================")



for form in soup.find_all("form"):


    print()

    print("ACTION:")

    print(
        form.get("action")
    )


    print("METHOD:")

    print(
        form.get("method")
    )


    print()

    print("INPUTS:")



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