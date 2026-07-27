import requests


base="http://192.168.14.134"


pages=[
"printdemo.html",
"demopage.html",
"demo.html",
"testpage.html",
"printertest.html",
"printtest.html",
"maintenance.html",
"service.html",
"diagnostics.html",
"diagnostic.html",
"reports.html",
"status.html",
"device.html",
"engine.html",
"setup.html",
"reset.html"
]


locations=[
"/cgi-bin/dynamic/printer/config/",
"/cgi-bin/dynamic/printer/config/reports/",
"/cgi-bin/dynamic/printer/config/gen/",
"/cgi-bin/dynamic/printer/"
]


for loc in locations:

    for p in pages:

        url=base+loc+p

        try:

            r=requests.get(
                url,
                timeout=3
            )

            if r.status_code != 404:

                print(
                    r.status_code,
                    len(r.text),
                    url
                )

        except:

            pass