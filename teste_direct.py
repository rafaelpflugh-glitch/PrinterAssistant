import requests


ip="192.168.14.134"


urls=[
"/cgi-bin/direct/printer/",
"/cgi-bin/direct/printer/index.html",
"/cgi-bin/direct/printer/remote",
"/cgi-bin/direct/printer/remoteOp",
"/cgi-bin/direct/printer/key",
"/cgi-bin/direct/printer/keyboard"
]


for u in urls:

    try:

        r=requests.get(
            "http://"+ip+u,
            timeout=10
        )

        print(
            r.status_code,
            u
        )

    except Exception as e:

        print(
            "ERRO",
            u,
            e
        )