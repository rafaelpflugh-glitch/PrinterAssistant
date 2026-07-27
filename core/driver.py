import requests


class Driver:

    def __init__(self, printer):

        self.printer = printer

        self.base = f"http://{printer.ip}"


    def get(self, endpoint, timeout=10):

        url = self.base + endpoint

        print()

        print("GET >", url)

        resposta = requests.get(
            url,
            timeout=timeout
        )

        print("STATUS:", resposta.status_code)

        return resposta


    def post(self, endpoint, dados=None, timeout=10):

        if dados is None:
            dados = {}

        url = self.base + endpoint

        print()

        print("POST >", url)
        print("DADOS >", dados)

        resposta = requests.post(
            url,
            data=dados,
            timeout=timeout
        )

        print("STATUS:", resposta.status_code)

        return resposta