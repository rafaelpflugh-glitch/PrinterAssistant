import requests

ip = "192.168.14.134"

url = (
    f"http://{ip}/cgi-bin/direct/printer/prtappse/semenu"
    "?page=clearlog"
    "&clearlogconfirmation=Yes"
)

r = requests.get(url, timeout=10)

print("STATUS:", r.status_code)
print("=" * 80)
print(r.text)