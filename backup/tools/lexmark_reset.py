import requests


BASE = "/cgi-bin/dynamic/printer/config/secure/"


def enviar_comando(ip, pagina, dados):

    url = f"http://{ip}{BASE}{pagina}"

    try:

        resposta = requests.post(
            url,
            data=dados,
            timeout=15
        )

        if resposta.status_code == 200:
            return True

        return False


    except Exception as erro:

        print(erro)

        return False



def reset_impressora(ip):

    return enviar_comando(
        ip,
        "restore_factory_settings.html",
        {
            "option": "base"
        }
    )



def reset_rede(ip):

    return enviar_comando(
        ip,
        "restore_factory_settings.html",
        {
            "option": "network"
        }
    )



def reset_apps(ip):

    return enviar_comando(
        ip,
        "restore_factory_settings.html",
        {
            "option": "les"
        }
    )