import requests
import re



def coletar_paginas(ip):


    paginas = [

        "/",
        "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",
        "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",
        "/cgi-bin/dynamic/printer/PrinterStatus.html",
        "/cgi-bin/sysdebugdata"

    ]


    textos = []


    for pagina in paginas:


        try:

            url = f"http://{ip}{pagina}"


            r = requests.get(
                url,
                timeout=5
            )


            if r.status_code == 200:


                print(
                    "OK:",
                    pagina
                )


                textos.append(
                    r.text
                )


        except Exception:


            pass



    return "\n".join(textos)




def extrair_info(ip):


    texto = coletar_paginas(ip)



    resultado = {


        "ip": ip,

        "modelo": None,

        "serial": None,

        "firmware": None,

        "fabricante": None

    }



    if "lexmark" in texto.lower():

        resultado["fabricante"]="Lexmark"



    # modelos Lexmark

    modelo = re.search(

        r"\b(MX|CX|MS|CS)\d{3}\b",

        texto,

        re.I

    )


    if modelo:

        resultado["modelo"] = modelo.group()




    # serial

    padroes_serial = [

        r"serial.{0,80}",

        r"serialnumber.{0,80}",

        r"device serial.{0,80}",

    ]



    for p in padroes_serial:


        achou = re.search(

            p,

            texto,

            re.I

        )


        if achou:


            resultado["serial"] = achou.group()

            break




    # firmware


    fw = re.search(

        r"firmware.{0,100}",

        texto,

        re.I

    )


    if fw:

        resultado["firmware"] = fw.group()



    return resultado