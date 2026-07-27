import requests

ip = "192.168.14.134"

url = f"http://{ip}/cgi-bin/dynamic/printer/include/jshelper.js"

r = requests.get(url)

print("STATUS:", r.status_code)

print()

print(r.text[:12000])