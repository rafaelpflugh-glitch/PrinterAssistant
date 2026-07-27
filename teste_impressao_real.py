import requests


ip = "192.168.14.134"


url = f"http://{ip}/cgi-bin/dynamic/printer/config/reports/MenusPage.html"


print("Testando:")
print(url)


r = requests.get(url)


print("STATUS:", r.status_code)

print(r.text[:1000])