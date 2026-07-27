import requests


ip = "192.168.14.134"


url = (
    f"http://{ip}"
    "/cgi-bin/dynamic/printer/config/reports/printdirectory.html"
)


print("==============================")
print("BAIXANDO HTML")
print("==============================")


r = requests.get(
    url,
    timeout=30
)


print(
    "STATUS:",
    r.status_code
)


with open(
    "data/printdirectory.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(r.text)


print(
    "SALVO data/printdirectory.html"
)


print()
print("==============================")
print("CONTEUDO")
print("==============================")


print(
    r.text[:3000]
)