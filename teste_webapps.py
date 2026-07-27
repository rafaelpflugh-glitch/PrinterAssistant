import requests

ip = "192.168.14.134"

urls = [

"/cgi-bin/direct/printer/prtapp/apps/webappsservlet",

"/cgi-bin/direct/printer/prtapp/apps/webappsservlet?menu",

"/cgi-bin/direct/printer/prtapp/apps/webappsservlet?action=list",

"/cgi-bin/direct/printer/prtapp/apps/webappsservlet?page=home",

"/cgi-bin/direct/printer/prtapp/apps/webappsservlet?help",

]

for u in urls:

    print("="*80)
    print(u)

    try:

        r = requests.get(
            f"http://{ip}{u}",
            timeout=8
        )

        print("STATUS:", r.status_code)
        print(r.text[:2000])

    except Exception as e:

        print(e)