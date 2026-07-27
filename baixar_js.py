import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

IP = "192.168.14.134"

url = f"http://{IP}/cgi-bin/dynamic/se_index.html"

r = requests.get(url, timeout=5)

print("Status:", r.status_code)

soup = BeautifulSoup(r.text, "html.parser")

print("\nArquivos JS encontrados:\n")

for script in soup.find_all("script", src=True):

    src = urljoin(url, script["src"])

    print(src)