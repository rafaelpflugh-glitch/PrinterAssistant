import requests



def enviar_post(ip, endpoint, dados):


    url = f"http://{ip}{endpoint}"


    try:


        resposta = requests.post(

            url,

            data=dados,

            timeout=10

        )


        if resposta.status_code == 200:


            return True, resposta.text



        else:


            return False, f"HTTP {resposta.status_code}"



    except Exception as erro:


        return False, str(erro)





def reset_fabrica(ip):


    endpoint = (
        "/cgi-bin/dynamic/printer/config/secure/"
        "restore_factory_settings.html"
    )


    dados = {

        "option":
        "base"

    }



    return enviar_post(
        ip,
        endpoint,
        dados
    )





def reset_rede(ip):


    endpoint = (
        "/cgi-bin/dynamic/printer/config/secure/"
        "restore_factory_settings.html"
    )


    dados = {

        "option":
        "network"

    }



    return enviar_post(
        ip,
        endpoint,
        dados
    )





def reset_apps(ip):


    endpoint = (
        "/cgi-bin/dynamic/printer/config/secure/"
        "restore_factory_settings.html"
    )


    dados = {

        "option":
        "les"

    }



    return enviar_post(
        ip,
        endpoint,
        dados
    )





def apagar_memoria(ip):


    endpoint = (
        "/cgi-bin/dynamic/printer/config/secure/"
        "erase_printer_memory.html"
    )


    dados = {

        "confirm":
        "confirm"

    }



    return enviar_post(
        ip,
        endpoint,
        dados
    )