import requests

ip = "192.168.14.134"

r = requests.get(
    f"http://{ip}/cgi-bin/script/printer/iop3"
)

print("HEADERS\n")

for k,v in r.headers.items():
    print(k,":",v)