import requests
import time


ip="192.168.14.134"


url=f"http://{ip}/cgi-bin/dynamic/printer/config/reports/MenusPage.html"


print()
print("==============================")
print("TESTANDO MENUS PAGE")
print("==============================")

print(url)


inicio=time.time()


try:

    r=requests.get(
        url,
        timeout=(5,60)
    )


    tempo=time.time()-inicio


    print()

    print("STATUS:")
    print(r.status_code)

    print()

    print("TEMPO:")
    print(round(tempo,2),"segundos")


    print()

    print("CONTENT TYPE:")
    print(
        r.headers.get(
            "Content-Type"
        )
    )


    print()

    print("TAMANHO:")
    print(
        len(r.content)
    )



    with open(
        "data/MenusPage.html",
        "wb"
    ) as f:

        f.write(
            r.content
        )


    print()

    print(
        "SALVO data/MenusPage.html"
    )



except Exception as erro:


    tempo=time.time()-inicio


    print()

    print("ERRO:")
    print(erro)

    print()

    print(
        "TEMPO:",
        round(tempo,2)
    )