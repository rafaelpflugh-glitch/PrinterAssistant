import requests

from tools.pages.endpoints import PAGINAS


def testar_endpoint(ip, endpoint):

    url = f"http://{ip}{endpoint}"

    try:

        r = requests.get(
            url,
            timeout=3
        )

        return r.status_code

    except:

        return None


def procurar_endpoints(ip):

    encontrados = {}

    for grupo, lista in PAGINAS.items():

        encontrados[grupo] = []

        for pagina in lista:

            status = testar_endpoint(ip, pagina)

            if status:

                encontrados[grupo].append(
                    (pagina, status)
                )

    return encontrados