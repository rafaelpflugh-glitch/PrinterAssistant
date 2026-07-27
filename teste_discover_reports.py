import requests


ip = "192.168.14.134"

base = f"http://{ip}"


possiveis = [

    "menusettings.html",

    "menus.html",

    "menu.html",

    "printmenus.html",

    "reports.html",

    "report.html",

    "network.html",

    "networksetup.html",

    "net.html",

    "supplies.html",

    "supply.html",

    "device.html",

    "deviceinfo.html",

    "configuration.html",

    "config.html",

    "settings.html",

    "printersettings.html"

]



print()

print("==============================")
print("DESCOBRINDO RELATÓRIOS")
print("==============================")



for nome in possiveis:


    url = (

        base +

        "/cgi-bin/dynamic/printer/config/reports/" +

        nome

    )


    try:

        r = requests.get(

            url,

            timeout=5

        )


        if r.status_code == 200:


            print()

            print("ENCONTRADO")

            print(url)

            print(
                "Titulo:"
            )


            inicio = r.text.find(
                "<title>"
            )


            fim = r.text.find(
                "</title>"
            )


            if inicio >= 0:

                print(
                    r.text[inicio+7:fim]
                )



    except:

        pass