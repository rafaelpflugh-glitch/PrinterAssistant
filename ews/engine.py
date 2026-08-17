import json
import os
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError


class EWSParser(HTMLParser):
    """
    Parser simples para descobrir FORM, INPUT, SELECT e OPTION
    em páginas EWS da impressora.
    """

    def __init__(self):
        super().__init__()

        self.forms = []
        self.current_form = None
        self.current_select = None
        self.current_option = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()

        if tag == "form":
            self.current_form = {
                "action": attrs.get("action", ""),
                "method": attrs.get("method", "GET").upper(),
                "fields": []
            }

            self.forms.append(self.current_form)

        elif tag == "input" and self.current_form is not None:
            self.current_form["fields"].append({
                "type": attrs.get("type", "text"),
                "name": attrs.get("name"),
                "id": attrs.get("id"),
                "value": attrs.get("value", ""),
                "checked": "checked" in attrs
            })

        elif tag == "select" and self.current_form is not None:
            self.current_select = {
                "type": "select",
                "name": attrs.get("name"),
                "id": attrs.get("id"),
                "options": []
            }

            self.current_form["fields"].append(self.current_select)

        elif tag == "option" and self.current_select is not None:
            self.current_option = {
                "value": attrs.get("value", ""),
                "selected": "selected" in attrs,
                "text": ""
            }

    def handle_data(self, data):
        if self.current_option is not None:
            self.current_option["text"] += data.strip()

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "option":
            if self.current_select is not None and self.current_option is not None:
                self.current_select["options"].append(self.current_option)

            self.current_option = None

        elif tag == "select":
            self.current_select = None

        elif tag == "form":
            self.current_form = None


class EWSClient:
    """
    Cliente básico para comunicação HTTP com o EWS.
    """

    def __init__(self, ip, timeout=10):
        self.ip = ip
        self.base_url = f"http://{ip}"
        self.timeout = timeout

    def build_url(self, path):
        if path.startswith("http://") or path.startswith("https://"):
            return path

        if not path.startswith("/"):
            path = "/" + path

        return self.base_url + path

    def get(self, path):
        url = self.build_url(path)

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "PrinterAssistant/1.0"
            }
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read()

            return {
                "status": response.status,
                "url": url,
                "headers": dict(response.headers),
                "body": body.decode("utf-8", errors="replace")
            }

    def post(self, path, data):
        url = self.build_url(path)

        encoded = urllib.parse.urlencode(data).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=encoded,
            method="POST",
            headers={
                "User-Agent": "PrinterAssistant/1.0",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read()

            return {
                "status": response.status,
                "url": url,
                "headers": dict(response.headers),
                "body": body.decode("utf-8", errors="replace")
            }

    def parse(self, html):
        parser = EWSParser()
        parser.feed(html)
        return parser.forms


class CommandEngine:
    """
    Motor genérico de comandos EWS.

    Um comando possui:

        name
        label
        endpoint
        method
        parameters
        verify

    O objetivo é que o Printer Assistant não precise conhecer
    diretamente os parâmetros internos da impressora.
    """

    def __init__(self, ip, registry_path=None):
        self.client = EWSClient(ip)

        if registry_path is None:
            registry_path = os.path.join(
                "ews",
                "maps",
                f"{ip}.json"
            )

        self.registry_path = registry_path
        self.registry = self.load_registry()

    def load_registry(self):
        if not os.path.exists(self.registry_path):
            return {
                "printer": self.client.ip,
                "commands": {}
            }

        try:
            with open(
                self.registry_path,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        except Exception:
            return {
                "printer": self.client.ip,
                "commands": {}
            }

    def save_registry(self):
        folder = os.path.dirname(self.registry_path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(
            self.registry_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.registry,
                f,
                indent=4,
                ensure_ascii=False
            )

    def discover_page(self, path):
        """
        Baixa uma página EWS e transforma os FORM/SELECT
        encontrados em um mapa legível.
        """

        response = self.client.get(path)

        html = response["body"]

        forms = self.client.parse(html)

        result = {
            "url": response["url"],
            "status": response["status"],
            "forms": forms
        }

        return result

    def save_discovery(self, name, discovery):
        path = os.path.join(
            "ews",
            "maps",
            f"{name}.json"
        )

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                discovery,
                f,
                indent=4,
                ensure_ascii=False
            )

        return path

    def register_command(
        self,
        name,
        label,
        endpoint,
        method,
        parameters,
        verify=None
    ):
        self.registry["commands"][name] = {
            "label": label,
            "endpoint": endpoint,
            "method": method.upper(),
            "parameters": parameters,
            "verify": verify
        }

        self.save_registry()

    def execute(self, name, values):
        if name not in self.registry["commands"]:
            raise ValueError(
                f"Comando não encontrado: {name}"
            )

        command = self.registry["commands"][name]

        parameters = {}

        for parameter in command["parameters"]:
            key = parameter["name"]

            if key in values:
                parameters[key] = values[key]

        method = command["method"]

        print()
        print("=" * 60)
        print("PRINTER ASSISTANT - COMMAND ENGINE")
        print("=" * 60)
        print()
        print("Comando :", name)
        print("Ação    :", command["label"])
        print("Método  :", method)
        print("Endpoint:", command["endpoint"])
        print()

        print("Payload:")

        for key, value in parameters.items():
            print(f"  {key} = {value}")

        print()

        if method == "POST":
            response = self.client.post(
                command["endpoint"],
                parameters
            )

        else:
            query = urllib.parse.urlencode(parameters)

            endpoint = command["endpoint"]

            if "?" in endpoint:
                endpoint += "&" + query
            else:
                endpoint += "?" + query

            response = self.client.get(endpoint)

        print("HTTP:", response["status"])

        if response["status"] == 200:
            print("[OK] Impressora respondeu HTTP 200.")

        return response


def print_discovery(discovery):
    print()
    print("=" * 70)
    print("PRINTER ASSISTANT - EWS DISCOVERY")
    print("=" * 70)

    print()
    print("URL:", discovery["url"])
    print("HTTP:", discovery["status"])
    print("FORMULÁRIOS:", len(discovery["forms"]))
    print()

    for form_number, form in enumerate(
        discovery["forms"],
        start=1
    ):
        print("-" * 70)

        print(f"FORM #{form_number}")
        print("ACTION:", form["action"])
        print("METHOD:", form["method"])

        print()

        for field in form["fields"]:

            if field["type"] == "select":

                print(
                    f"SELECT: {field['name']}"
                )

                for option in field["options"]:

                    selected = ""

                    if option["selected"]:
                        selected = " [ATUAL]"

                    print(
                        f"    {option['value']} = "
                        f"{option['text']}{selected}"
                    )

            else:

                print(
                    f"{field['type'].upper()}: "
                    f"{field['name']} = "
                    f"{field['value']}"
                )

    print()