import socket
import requests
import concurrent.futures
import re


from core.contexto import atualizar





# ==================================================
# DESCOBRE REDE LOCAL
# ==================================================

def descobrir_rede():


    try:

        hostname = socket.gethostname()

        ip_local = socket.gethostbyname(
            hostname
        )

        partes = ip_local.split(".")


        return ".".join(partes[:3])


    except Exception:


        return "192.168.1"







# ==================================================
# TESTA IP
# ==================================================

def testar_ip(ip):


    resultado = {

        "ip": ip,

        "serial": None,

        "modelo": None,

        "firmware": None

    }



    try:


        url = (
            f"http://{ip}/cgi-bin/sysdebugdata"
        )



        resposta = requests.get(

            url,

            timeout=4

        )



        if resposta.status_code != 200:

            return None





        texto = resposta.text





        if "Printer Serial Number" not in texto:

            return None






        serial = re.search(

            r"Printer Serial Number:\s*(\S+)",

            texto

        )



        if serial:


            resultado["serial"] = (
                serial.group(1)
            )






        modelos = [

            r"Model Name:\s*(.+)",

            r"Printer Model:\s*(.+)",

            r"Device Model:\s*(.+)"

        ]



        for padrao in modelos:


            modelo = re.search(

                padrao,

                texto,

                re.IGNORECASE

            )


            if modelo:


                resultado["modelo"] = (

                    modelo.group(1)

                    .strip()

                )


                break






        firmware = re.search(

            r"RIP Firmware Version.*?\n(.+)",

            texto

        )



        if firmware:


            resultado["firmware"] = (

                firmware.group(1)

                .strip()

            )





        return resultado





    except Exception:


        return None







# ==================================================
# PROCURA IMPRESSORAS NA REDE
# ==================================================

def procurar_impressora():


    rede = descobrir_rede()



    print(
        f"\nProcurando na rede {rede}.x\n"
    )



    ips = [

        f"{rede}.{i}"

        for i in range(1,255)

    ]



    encontradas = []





    with concurrent.futures.ThreadPoolExecutor(

        max_workers=80

    ) as executor:



        resultados = executor.map(

            testar_ip,

            ips

        )



        for resultado in resultados:


            if resultado:


                encontradas.append(

                    resultado

                )



    return encontradas







# ==================================================
# GERENCIADOR DE DESCOBERTA
# ==================================================

def procurar():



    impressoras = procurar_impressora()





    if not impressoras:


        return """

Nenhuma impressora Lexmark encontrada.

"""







    # guarda lista para seleção manual

    atualizar({

        "impressoras_encontradas":

        impressoras

    })







    # somente uma impressora

    if len(impressoras) == 1:


        imp = impressoras[0]



        atualizar({

            "ip":
            imp.get("ip"),


            "serial":
            imp.get("serial"),


            "modelo":
            imp.get("modelo"),


            "firmware":
            imp.get("firmware")

        })



        return f"""

Uma impressora encontrada.

Selecionada automaticamente.


IP:

{imp.get('ip')}


Modelo:

{imp.get('modelo')}


Serial:

{imp.get('serial')}


Firmware:

{imp.get('firmware')}


Contexto atualizado.

"""







    # várias impressoras


    texto = """

Foram encontradas várias impressoras:


"""



    for indice, imp in enumerate(

        impressoras,

        start=1

    ):



        texto += f"""

{indice}


IP:

{imp.get('ip')}


Modelo:

{imp.get('modelo')}


Serial:

{imp.get('serial')}


Firmware:

{imp.get('firmware')}



"""





    texto += """

Use:

selecionar numero


Exemplo:

selecionar 2

"""



    return texto