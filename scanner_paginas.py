import requests

IP = "192.168.14.134"

base = f"http://{IP}/cgi-bin/dynamic/config/gen/"

paginas = [
    "setuppg.html",
    "demopg.html",
    "demo.html",
    "testpage.html",
    "printer.html",
    "reports.html",
    "report.html",
    "config.html",
    "configpg.html",
    "network.html",
    "asset.html",
    "assetpg.html",
    "menu.html",
    "menupg.html",
    "diag.html",
    "status.html",
    "supplies.html",
    "device.html"
]

for pagina in paginas:

    try:

        r = requests.get(base + pagina, timeout=3)

        if r.status_code != 404:
            print(r.status_code, pagina)

    except:
        pass