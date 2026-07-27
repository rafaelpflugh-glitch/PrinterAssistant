import requests


ip="192.168.14.134"


url=f"http://{ip}/cgi-bin/dynamic/printer/config/reports/"


r=requests.get(
    url,
    timeout=10
)


print(
    "STATUS:",
    r.status_code
)


print(
    r.text[:1000]
)