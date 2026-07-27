import requests


ip="192.168.14.134"

url=f"http://{ip}/cgi-bin/dynamic/printer/config/reports/printdirectory.html"


r=requests.get(
    url,
    timeout=30
)


print("STATUS:",r.status_code)

print("TIPO:",r.headers.get("Content-Type"))

print("TAMANHO:",len(r.content))


open(
    "data/printdirectory.html",
    "wb"
).write(r.content)


print("SALVO")
