import requests


ip="192.168.14.134"


url=(
    f"http://{ip}"
    "/cgi-bin/dynamic/printer/config/vncviewer.html"
)


print("==============================")
print("VNC VIEWER")
print("==============================")


r=requests.get(
    url,
    timeout=30
)


print(
    "STATUS:",
    r.status_code
)


print(
    "TAMANHO:",
    len(r.text)
)


open(
    "data/vncviewer.html",
    "w",
    encoding="utf-8"
).write(
    r.text
)


print()
print("==============================")
print("CONTEUDO")
print("==============================")


print(
    r.text
)