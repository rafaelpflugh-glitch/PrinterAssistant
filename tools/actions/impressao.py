import requests

from tools.pages.endpoints import PAGINAS


def imprimir(ip, tipo):

    if tipo not in PAGINAS:

        return False, "ação inexistente"

    for endpoint in PAGINAS[tipo]:

        try:

            url = f"http://{ip}{endpoint}"

            r = requests.get(
                url,
                timeout=5
            )

            if r.status_code == 200:

                return True, endpoint

        except:
            pass

    return False, "nenhum endpoint respondeu"