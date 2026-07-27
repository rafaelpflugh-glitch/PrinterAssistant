import requests


ip="192.168.14.134"


url=(
    f"http://{ip}"
    "/cgi-bin/dynamic/printer/applets/remoteOp/vncviewer.jar"
)


print("==============================")
print("BAIXANDO VNC JAR")
print("==============================")


r=requests.get(
    url,
    timeout=30
)


print(
    "STATUS:",
    r.status_code
)


print(
    "TIPO:",
    r.headers.get("Content-Type")
)


print(
    "TAMANHO:",
    len(r.content)
)


if r.status_code == 200:

    open(
        "data/vncviewer.jar",
        "wb"
    ).write(
        r.content
    )

    print(
        "SALVO"
    )