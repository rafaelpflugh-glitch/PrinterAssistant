import requests

ip = "192.168.14.134"

urls = [

"/cgi-bin/direct/printer/prtappse/semenu?page=clearlog",

"/cgi-bin/direct/printer/prtappse/semenu?page=setloglevel",

"/cgi-bin/direct/printer/prtappse/semenu?page=bundles"

]

for u in urls:

    print("="*70)
    print(u)

    r = requests.get(
        f"http://{ip}{u}",
        timeout=5
    )

    print("STATUS:", r.status_code)
    print(r.text[:3000])