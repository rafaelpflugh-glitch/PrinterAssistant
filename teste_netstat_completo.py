import requests

ip="192.168.14.134"

r=requests.get(
    f"http://{ip}/cgi-bin/script/printer/iop3",
    timeout=10
)

print(r.text)