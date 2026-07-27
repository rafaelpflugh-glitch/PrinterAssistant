import requests


ip = "192.168.1.1"


url = f"http://{ip}/cgi-bin/dynamic/printer/PrinterStatus.html"


try:

    r = requests.get(
        url,
        timeout=5
    )


    print("STATUS:", r.status_code)

    print()

    print(r.text[:1000])


except Exception as e:

    print(e)