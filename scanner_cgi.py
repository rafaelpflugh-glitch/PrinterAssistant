import requests

IP="192.168.14.134"

paths=[
"/cgi-bin/",
"/cgi-bin/dynamic/",
"/cgi-bin/dynamic/config/",
"/cgi-bin/printer/",
"/cgi-bin/lpm/",
"/cgi-bin/status/",
"/cgi-bin/webglue/",
"/cgi-bin/print/",
"/cgi-bin/reports/"
]


for p in paths:

    try:

        r=requests.get(
            "http://"+IP+p,
            timeout=3
        )

        print(
            r.status_code,
            p,
            len(r.text)
        )

    except Exception as e:
        print("ERRO",p)