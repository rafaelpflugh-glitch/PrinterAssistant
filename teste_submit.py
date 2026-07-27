import requests

ip = "192.168.14.134"

url = f"http://{ip}/cgi-bin/direct/printer/prtappse/semenu"

dados = {
    "page": "clearlog",
    "clearlogconfirmation": "Yes"
}

r = requests.post(url, data=dados, timeout=5)

print("STATUS:", r.status_code)
print(r.text[:4000])