import requests
import re



def identificar(ip):


    dados = {

        "ip": ip,

        "fabricante": None,

        "modelo": None,

        "serial": None,

        "firmware": None

    }



    paginas = [

        "/",

        "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html",

        "/cgi-bin/dynamic/printer/config/reports/devicestatistics.html",

        "/cgi-bin/dynamic/printer/PrinterStatus.html"

    ]



    textos = []



    for pagina in paginas:


        try:


            r = requests.get(

                f"http://{ip}{pagina}",

                timeout=3

            )


            if r.status_code == 200:

                textos.append(
                    r.text
                )


        except:

            pass



    texto = "\n".join(textos)



    baixo = texto.lower()



    if "lexmark" in baixo:

        dados["fabricante"] = "Lexmark"



    # tenta encontrar modelo


    padroes_modelo = [

        r"MX\d+",

        r"CX\d+",

        r"MS\d+",

        r"MB\d+",

        r"CS\d+"

    ]



    for p in padroes_modelo:


        encontrado = re.search(
            p,
            texto,
            re.I
        )


        if encontrado:


            dados["modelo"] = encontrado.group()

            break




    # serial


    procura_serial = re.findall(

        r"serial.{0,50}",

        texto,

        re.I

    )


    if procura_serial:

        dados["serial"] = procura_serial[0]



    return dados