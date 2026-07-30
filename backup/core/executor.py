import requests


class Executor:

    def __init__(self, printer):

        self.printer = printer

        self.timeout = 10

    def get(self, endpoint):

        url = f"http://{self.printer.ip}{endpoint}"

        print(f"\nGET -> {url}")

        r = requests.get(
            url,
            timeout=self.timeout
        )

        print("STATUS:", r.status_code)

        return r

    def post(self, endpoint, dados=None):

        url = f"http://{self.printer.ip}{endpoint}"

        print(f"\nPOST -> {url}")

        if dados is None:
            dados = {}

        r = requests.post(
            url,
            data=dados,
            timeout=self.timeout
        )

        print("STATUS:", r.status_code)

        return r