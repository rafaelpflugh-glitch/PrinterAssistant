import requests

from tools.pages.endpoints import PAGINAS


def testar_usb(ip):

    for endpoint in PAGINAS["usb"]:

        try:

            r = requests.get(
                f"http://{ip}{endpoint}",
                timeout=3
            )

            if r.status_code == 200:

                return "USB HOST detectado"

        except:
            pass

    return "USB não detectado"