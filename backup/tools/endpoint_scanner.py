import requests



ENDPOINTS = {


    ENDPOINTS = {


"SysDebug":
"/cgi-bin/sysdebugdata",


"Status":
"/cgi-bin/status.html",


"Config":
"/cgi-bin/config.html",


"Settings":
"/cgi-bin/settings.html",


"Asset":
"/cgi-bin/asset.html",


"Menus":
"/cgi-bin/menu.html",


"DeviceInfo":
"/cgi-bin/deviceinfo.html",


"Printer":
"/cgi-bin/printer.html",


"EWS":
"/",


"WebService":
"/cgi-bin/webservice",


"SNMP":
"/cgi-bin/snmp"




}





def explorar(ip):


    resultados = []


    resultados.append(
        "\n=============================="
    )

    resultados.append(
        "LEXMARK ENDPOINT SCANNER"
    )

    resultados.append(
        "==============================\n"
    )



    for nome, endpoint in ENDPOINTS.items():


        url = f"http://{ip}{endpoint}"


        try:


            r = requests.get(
                url,
                timeout=5
            )



            if r.status_code != 404:


                resultados.append(
                    f"✓ {nome:<15} {r.status_code}  {endpoint}"
                )


            else:


                resultados.append(
                    f"✗ {nome:<15} 404"
                )



        except Exception as erro:


            resultados.append(
                f"? {nome:<15} ERRO"
            )



    return "\n".join(resultados)