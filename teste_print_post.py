import requests
from bs4 import BeautifulSoup

ip = "192.168.14.134"

url = f"http://{ip}/cgi-bin/dynamic/printer/config/reports/MenusPage.html"

html = requests.get(url).text

print("="*60)

print("FORMS")

print("="*60)

soup = BeautifulSoup(html,"html.parser")

for form in soup.find_all("form"):

    print()

    print("ACTION :",form.get("action"))

    print("METHOD :",form.get("method"))

    print()

    for i in form.find_all("input"):

        print(i)

    for s in form.find_all("select"):

        print(s)