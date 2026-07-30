import requests


class Lexmark:

    def __init__(self, ip):

        self.ip = ip

        self.base = f"http://{ip}"

        self.session = requests.Session()

    def post(self, action, data):

        url = self.base + action

        print("="*60)
        print("POST")
        print(url)
        print("="*60)

        print("DADOS")

        for k,v in data.items():
            print(k,"=",v)

        print()

        r = self.session.post(
            url,
            data=data,
            timeout=10
        )

        print("STATUS:",r.status_code)

        print("RESPOSTA")

        print(r.text[:500])

        return r