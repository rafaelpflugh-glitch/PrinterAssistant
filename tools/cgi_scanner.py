import requests


base="http://192.168.14.134"


paths=[
"/cgi-bin/posttest/",
"/cgi-bin/postpf/",
"/cgi-bin/direct/",
"/cgi-bin/direct/printer/",
"/cgi-bin/dynamic/printer/config/",
"/cgi-bin/dynamic/printer/config/gen/",
"/cgi-bin/dynamic/printer/config/reports/"
]


for p in paths:

    url=base+p

    try:

        r=requests.get(
            url,
            timeout=5
        )

        print(
            r.status_code,
            url,
            len(r.text)
        )

    except Exception as e:

        print(
            "ERRO",
            url,
            e
        )