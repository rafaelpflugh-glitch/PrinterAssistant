import requests

ip = "192.168.14.134"

url = f"http://{ip}/cgi-bin/script/printer/iop3"

r = requests.get(url)

print(r.status_code)
print()
print(r.text[:5000])