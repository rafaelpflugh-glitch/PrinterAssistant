
import sys
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote


class EWSParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.forms = []
        self.current_form = None
        self.current_select = None
        self.current_option = None

    def handle_starttag(self, tag, attrs):

        attrs = dict(attrs)

        if tag.lower() == "form":

            self.current_form = {
                "action": attrs.get("action", ""),
                "method": attrs.get("method", "GET").upper(),
                "fields": []
            }

            self.forms.append(self.current_form)

        elif tag.lower() == "input" and self.current_form:

            self.current_form["fields"].append({
                "type": "input",
                "name": attrs.get("name"),
                "value": attrs.get("value", ""),
                "id": attrs.get("id"),
                "checked": "checked" in attrs
            })

        elif tag.lower() == "select" and self.current_form:

            self.current_select = {
                "type": "select",
                "name": attrs.get("name"),
                "id": attrs.get("id"),
                "options": []
            }

            self.current_form["fields"].append(self.current_select)

        elif tag.lower() == "option" and self.current_select:

            self.current_option = {
                "value": attrs.get("value", ""),
                "text": "",
                "selected": "selected" in attrs
            }

            self.current_select["options"].append(self.current_option)

    def handle_data(self, data):

        if self.current_option is not None:
            self.current_option["text"] += data.strip()

    def handle_endtag(self, tag):

        tag = tag.lower()

        if tag == "option":
            self.current_option = None

        elif tag == "select":
            self.current_select = None

        elif tag == "form":
            self.current_form = None


def parse_file(path):

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT - EWS REVERSE ENGINEER")
    print("=" * 70)
    print()
    print(f"Arquivo: {path.name}")
    print(f"Caminho: {path}")
    print()

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception as e:
        print(f"[ERRO] Não foi possível ler o arquivo: {e}")
        return

    parser = EWSParser()

    try:
        parser.feed(text)
    except Exception as e:
        print(f"[ERRO] Falha analisando HTML: {e}")
        return

    print(f"FORMULÁRIOS ENCONTRADOS: {len(parser.forms)}")
    print()

    if not parser.forms:
        print("Nenhum <form> encontrado.")
        print()
        print("Isso pode acontecer se a página utilizar JavaScript")
        print("ou outro mecanismo para enviar os dados.")
        return

    for form_number, form in enumerate(parser.forms, 1):

        print("-" * 70)
        print(f"FORM #{form_number}")
        print("-" * 70)

        print(f"METHOD : {form['method']}")
        print(f"ACTION : {form['action']}")
        print()

        print(f"CAMPOS: {len(form['fields'])}")
        print()

        for field in form["fields"]:

            if field["type"] == "input":

                print(f"INPUT")
                print(f"  name     = {field['name']}")
                print(f"  id       = {field['id']}")
                print(f"  value    = {field['value']}")
                print(f"  checked  = {field['checked']}")
                print()

            elif field["type"] == "select":

                print("SELECT")
                print(f"  name = {field['name']}")
                print(f"  id   = {field['id']}")

                print("  OPTIONS:")

                for option in field["options"]:

                    marker = "* " if option["selected"] else "  "

                    print(
                        f"    {marker}"
                        f"{option['value']!r}"
                        f" -> "
                        f"{option['text']!r}"
                    )

                print()


def main():

    if len(sys.argv) < 2:

        print()
        print("Uso:")
        print()
        print("  python tools\\ews_reverse.py arquivo.html")
        print()
        print("Exemplo:")
        print()
        print(
            "  python tools\\ews_reverse.py "
            "paperweight.html"
        )
        print()

        return

    path = Path(sys.argv[1])

    if not path.exists():

        print()
        print(f"[ERRO] Arquivo não encontrado:")
        print(path)
        print()

        return

    parse_file(path)


if __name__ == "__main__":
    main()

