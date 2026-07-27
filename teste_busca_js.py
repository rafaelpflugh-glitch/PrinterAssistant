import requests

ip = "192.168.14.134"

texto = requests.get(
    f"http://{ip}/cgi-bin/dynamic/printer/include/jshelper.js"
).text

palavras = [
    "submit",
    "print",
    "post",
    "form",
    "action",
    "report",
    "menu",
    "device",
    "location",
    "window.location",
    "XMLHttpRequest",
    "fetch",
    "cgi-bin",
]

for palavra in palavras:

    if palavra.lower() in texto.lower():
        print("Encontrado:", palavra)