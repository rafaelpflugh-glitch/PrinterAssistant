import requests

from tools.pages.endpoints import PAGINAS


def executar_reset(ip, tipo):

    if tipo not in PAGINAS:

        return False

    for endpoint in PAGINAS[tipo]:

        try:

            r = requests.get(
                f"http://{ip}{endpoint}",
                timeout=5
            )

            if r.status_code == 200:

                return True

        except:
            pass

    return False