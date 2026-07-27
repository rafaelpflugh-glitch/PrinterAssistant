import socket
import requests
from concurrent.futures import ThreadPoolExecutor


def descobrir_rede():

    nome = socket.gethostname()

    ip = socket.gethostbyname(nome)

    partes = ip.split(".")

    rede = ".".join(partes[:3])

    return rede



def testar_impressora(ip):

    endpoints = [

        "/",
        "/cgi-bin/dynamic/printer/PrinterStatus.html",
        "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html"

    ]


    for endpoint in endpoints:

        try:

            url = f"http://{ip}{endpoint}"

            r = requests.get(
                url,
                timeout=1
            )


            if r.status_code == 200:


                texto = r.text.lower()


                sinais = [

                    "lexmark",
                    "printer",
                    "printerstatus",
                    "toner",
                    "supplies",
                    "ews"

                ]


                for s in sinais:

                    if s in texto:


                        return {

                            "ip": ip,

                            "endpoint": endpoint

                        }



        except:

            pass



    return None





def detectar():

    rede = descobrir_rede()


    print()

    print("Rede detectada:")

    print(
        rede + ".x"
    )


    print()

    print(
        "Procurando impressoras..."
    )



    ips = [

        f"{rede}.{i}"

        for i in range(1,255)

    ]



    encontradas=[]



    with ThreadPoolExecutor(
        max_workers=64
    ) as executor:


        resultados = executor.map(
            testar_impressora,
            ips
        )



        for r in resultados:


            if r:

                encontradas.append(r)



    return encontradas