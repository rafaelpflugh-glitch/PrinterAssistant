import requests


ip = "192.168.14.134"


endpoints = [

"/cgi-bin/printer/demo",

"/cgi-bin/printer/demopage",

"/cgi-bin/printer/test",

"/cgi-bin/printer/testpage",

"/cgi-bin/printer/config",

"/cgi-bin/printer/configuration",

"/cgi-bin/printer/configpage",

"/cgi-bin/printer/menus",

"/cgi-bin/printer/menu",

"/cgi-bin/printer/asset",

"/cgi-bin/printer/status",

"/cgi-bin/status",

"/cgi-bin/panel",

"/cgi-bin/sysdebugdata"

]


print("==============================")
print("SCAN ENDPOINTS LEXMARK")
print("==============================")


for ep in endpoints:


    url = f"http://{ip}{ep}"


    try:


        r = requests.get(
            url,
            timeout=3
        )


        if r.status_code != 404:


            print(
                "OK",
                r.status_code,
                ep
            )


        else:


            print(
                "404",
                ep
            )



    except Exception as e:


        print(
            "ERRO",
            ep,
            e
        )