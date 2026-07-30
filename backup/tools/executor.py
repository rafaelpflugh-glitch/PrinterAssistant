import requests


class Executor:

    def __init__(self, ip):

        self.ip = ip

        self.timeout = 10


    def abrir(self, endpoint):

        url = f"http://{self.ip}{endpoint}"

        print(f"\nGET -> {url}")

        try:

            r = requests.get(
                url,
                timeout=self.timeout
            )

            print("STATUS:", r.status_code)

            return r

        except Exception as erro:

            print(erro)

            return None


    def enviar(self, endpoint, dados):

        url = f"http://{self.ip}{endpoint}"

        print(f"\nPOST -> {url}")

        print(dados)

        try:

            r = requests.post(
                url,
                data=dados,
                timeout=self.timeout
            )

            print("STATUS:", r.status_code)

            return r

        except Exception as erro:

            print(erro)

            return None