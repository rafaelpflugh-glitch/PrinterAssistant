import requests


def coletar_debug(ip):

    url = f"http://{ip}/cgi-bin/sysdebugdata"


    try:

        r = requests.get(
            url,
            timeout=5
        )


        if r.status_code == 200:

            return r.text


        return None


    except Exception:

        return None