import requests

IP = "192.168.14.134"

url = f"http://{IP}/cgi-bin/dynamic/se_index.html"

r = requests.get(url)

with open(
    "se_index.html",
    "w",
    encoding="utf-8",
    errors="ignore"
) as f:

    f.write(r.text)

print("HTML salvo.")