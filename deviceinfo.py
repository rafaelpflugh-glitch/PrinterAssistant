import requests
from bs4 import BeautifulSoup


def get_device_info(ip):

    url = f"http://{ip}/cgi-bin/dynamic/printer/config/reports/deviceinfo.html"

    r = requests.get(url, timeout=5)

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    info = {}

    rows = soup.find_all("tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) >= 2:
            chave = cols[0].get_text(strip=True)
            valor = cols[1].get_text(strip=True)

            if chave:
                info[chave] = valor.replace("=", "").strip()

    return info