import requests



def explorar(ip):


    base = f"http://{ip}"



    caminhos = [

        "/cgi-bin/sysdebugdata",

        "/cgi-bin/dynamic/printer/config/",

        "/cgi-bin/dynamic/printer/reports/",

        "/cgi-bin/dynamic/printer/status/",

        "/cgi-bin/dynamic/printer/reports/configuration",

        "/cgi-bin/dynamic/printer/reports/configuration.html",

        "/cgi-bin/dynamic/printer/reports/device",

        "/cgi-bin/dynamic/printer/reports/device.html"

    ]



    resultado = []


    resultado.append(
        "========== EWS LEXMARK EXPLORER =========="
    )


    resultado.append(
        f"IP analisado: {ip}"
    )


    resultado.append(
        "\nPÁGINAS:"
    )



    for caminho in caminhos:


        try:


            resposta = requests.get(

                base + caminho,

                timeout=5

            )


            if resposta.status_code == 200:


                resultado.append(

                    f"[OK] {caminho}"

                )


            else:


                resultado.append(

                    f"[{resposta.status_code}] {caminho}"

                )



        except Exception:


            resultado.append(

                f"[ERRO] {caminho}"

            )



    resultado.append(

        "\n=========================================="

    )



    return "\n".join(resultado)