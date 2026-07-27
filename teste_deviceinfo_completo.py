import requests
from bs4 import BeautifulSoup

ip = "192.168.14.134"

url = f"http://{ip}/cgi-bin/dynamic/printer/config/reports/deviceinfo.html"

html = requests.get(url).text

print("="*70)
print("STATUS:", requests.get(url).status_code)
print("="*70)

soup = BeautifulSoup(html, "html.parser")

print("\nFORMS\n")

for form in soup.find_all("form"):
    print("ACTION:", form.get("action"))
    print("METHOD:", form.get("method"))

    for tag in form.find_all(["input","button","select"]):
        print(tag)

print("\n")
print("="*70)
print("LINKS")
print("="*70)

for a in soup.find_all("a"):
    print(a.get("href"))

print("\n")
print("="*70)
print("SCRIPTS")
print("="*70)

for s in soup.find_all("script"):
    if s.get("src"):
        print("SRC:", s["src"])
    else:
        texto = s.get_text().strip()
        if texto:
            print(texto[:300])

print("\n")
print("="*70)
print("ONCLICK")
print("="*70)

for tag in soup.find_all(True):
    if tag.get("onclick"):
        print(tag["onclick"])