import requests


ip = "192.168.14.134"

base = f"http://{ip}"


paginas = [

    "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",

    "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",

    "/cgi-bin/dynamic/printer/config/reports/menu.html",

    "/cgi-bin/dynamic/printer/config/reports/demo.html",

    "/cgi-bin/dynamic/printer/config/reports/index.html"

]


for pagina in paginas:


    url = base + pagina


    print()
    print("==============================")
    print(url)


    try:

        r = requests.get(
            url,
            timeout=10
        )


        print(
            "STATUS:",
            r.status_code
        )


        if r.status_code == 200:


            nome = pagina.split("/")[-1]


            with open(

                "data/" + nome,

                "w",

                encoding="utf-8"

            ) as f:

                f.write(
                    r.text
                )


            print(
                "SALVO"
            )


    except Exception as e:


        print(
            e
        )