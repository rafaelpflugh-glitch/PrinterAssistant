import sys
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class EWSCommandError(Exception):
    pass


class EWSFormExecutor:
    def __init__(self, printer_ip, page, timeout=10):
        self.printer_ip = printer_ip
        self.base_url = f"http://{printer_ip}"
        self.page = page
        self.url = urljoin(self.base_url, page)
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PrinterAssistant/1.0"
        })

    # ==========================================================
    # HTTP
    # ==========================================================

    def get(self):
        response = self.session.get(
            self.url,
            timeout=self.timeout
        )

        self._fix_encoding(response)

        if response.status_code != 200:
            raise EWSCommandError(
                f"HTTP {response.status_code} ao acessar {self.url}"
            )

        return response

    def post(self, action, payload):
        response = self.session.post(
            action,
            data=payload,
            timeout=self.timeout
        )

        self._fix_encoding(response)

        return response

    @staticmethod
    def _fix_encoding(response):
        """
        Alguns EWS Lexmark não informam corretamente UTF-8.
        O requests pode interpretar caracteres como OfÃ­cio.
        """
        try:
            if response.apparent_encoding:
                response.encoding = response.apparent_encoding
        except Exception:
            pass

    # ==========================================================
    # PARSE
    # ==========================================================

    def parse_form(self, html):
        soup = BeautifulSoup(html, "html.parser")

        form = soup.find("form")

        if not form:
            raise EWSCommandError(
                f"Nenhum <form> encontrado em {self.url}"
            )

        action = form.get("action", "").strip()

        if not action:
            action = self.url
        else:
            action = urljoin(self.url, action)

        method = form.get("method", "GET").upper()

        fields = []

        # ------------------------------------------------------
        # SELECT
        # ------------------------------------------------------

        for element in form.find_all("select"):
            name = element.get("name")

            if not name:
                continue

            options = []

            for option in element.find_all("option"):
                value = option.get("value", "")
                text = option.get_text(" ", strip=True)

                selected = option.has_attr("selected")

                options.append({
                    "value": value,
                    "text": text,
                    "selected": selected
                })

            current = next(
                (x for x in options if x["selected"]),
                options[0] if options else None
            )

            fields.append({
                "type": "select",
                "name": name,
                "value": current["value"] if current else "",
                "text": current["text"] if current else "",
                "options": options
            })

        # ------------------------------------------------------
        # INPUT
        # ------------------------------------------------------

        for element in form.find_all("input"):
            name = element.get("name")

            if not name:
                continue

            input_type = element.get("type", "text").lower()

            # Botões não fazem parte do estado.
            if input_type in (
                "submit",
                "reset",
                "button",
                "image"
            ):
                continue

            value = element.get("value", "")

            checked = element.has_attr("checked")

            field = {
                "type": input_type,
                "name": name,
                "value": value,
                "text": "",
                "checked": checked
            }

            fields.append(field)

        # ------------------------------------------------------
        # TEXTAREA
        # ------------------------------------------------------

        for element in form.find_all("textarea"):
            name = element.get("name")

            if not name:
                continue

            fields.append({
                "type": "textarea",
                "name": name,
                "value": element.text,
                "text": "",
                "checked": False
            })

        return {
            "url": self.url,
            "action": action,
            "method": method,
            "fields": fields
        }

    # ==========================================================
    # FORM DATA
    # ==========================================================

    def build_payload(self, form, changes):
        """
        Monta o POST preservando todos os campos originais.

        changes:
            {
                "0.system.49": "A5",
                "0.system.52": "Etiquetas"
            }
        """

        payload = []

        change_map = {}

        for name, requested in changes.items():
            change_map[name] = requested

        # ------------------------------------------------------
        # Campos normais
        # ------------------------------------------------------

        for field in form["fields"]:
            name = field["name"]
            field_type = field["type"]

            # ==================================================
            # SELECT
            # ==================================================

            if field_type == "select":

                value = field["value"]

                if name in change_map:
                    value = self.resolve_select_value(
                        field,
                        change_map[name]
                    )

                payload.append((name, value))

            # ==================================================
            # CHECKBOX
            # ==================================================

            elif field_type == "checkbox":

                checked = field.get("checked", False)

                if name in change_map:
                    checked = self.parse_bool(
                        change_map[name]
                    )

                if checked:
                    payload.append(
                        (name, field.get("value", "1"))
                    )

            # ==================================================
            # RADIO
            # ==================================================

            elif field_type == "radio":

                # Só enviamos o radio selecionado.
                if name in change_map:
                    requested = str(change_map[name])

                    if str(field.get("value", "")) == requested:
                        payload.append(
                            (name, field.get("value", ""))
                        )

                elif field.get("checked"):
                    payload.append(
                        (name, field.get("value", ""))
                    )

            # ==================================================
            # HIDDEN
            # ==================================================

            elif field_type == "hidden":

                value = field.get("value", "")

                if name in change_map:
                    value = str(change_map[name])

                payload.append((name, value))

            # ==================================================
            # TEXT / NUMBER / PASSWORD ETC
            # ==================================================

            else:

                value = field.get("value", "")

                if name in change_map:
                    value = str(change_map[name])

                payload.append((name, value))

        # ======================================================
        # Campos alterados que eventualmente não existam?
        # ======================================================

        existing_names = {
            field["name"]
            for field in form["fields"]
        }

        for name, value in changes.items():

            if name not in existing_names:
                raise EWSCommandError(
                    f"Campo '{name}' não existe no formulário."
                )

        return payload

    # ==========================================================
    # RESOLVE SELECT
    # ==========================================================

    @staticmethod
    def resolve_select_value(field, requested):

        requested = str(requested)

        # Primeiro tenta pelo valor real.
        for option in field["options"]:
            if str(option["value"]) == requested:
                return option["value"]

        # Depois tenta pelo texto exibido.
        normalized = requested.strip().lower()

        for option in field["options"]:
            text = option["text"].strip().lower()

            if text == normalized:
                return option["value"]

        # Também aceita comparação parcial.
        for option in field["options"]:
            text = option["text"].strip().lower()

            if normalized in text:
                return option["value"]

        raise EWSCommandError(
            f"Valor '{requested}' não encontrado no SELECT "
            f"'{field['name']}'."
        )

    # ==========================================================
    # BOOLEAN
    # ==========================================================

    @staticmethod
    def parse_bool(value):

        if isinstance(value, bool):
            return value

        value = str(value).strip().lower()

        true_values = {
            "1",
            "true",
            "yes",
            "sim",
            "on",
            "checked",
            "ativar",
            "ativado"
        }

        false_values = {
            "0",
            "false",
            "no",
            "não",
            "nao",
            "off",
            "unchecked",
            "desativar",
            "desativado"
        }

        if value in true_values:
            return True

        if value in false_values:
            return False

        raise EWSCommandError(
            f"Valor booleano inválido: {value}"
        )

    # ==========================================================
    # INSPECT
    # ==========================================================

    def inspect(self):

        response = self.get()

        form = self.parse_form(response.text)

        print()
        print("=" * 70)
        print("EWS FORM INSPECTOR")
        print("=" * 70)

        print()
        print(f"URL    : {form['url']}")
        print(f"ACTION : {form['action']}")
        print(f"METHOD : {form['method']}")
        print(f"CAMPOS : {len(form['fields'])}")

        for field in form["fields"]:

            print()

            field_type = field["type"]
            name = field["name"]

            if field_type == "select":

                print(f"SELECT   {name}")
                print(f"         valor atual: {field['value']}")
                print(f"         texto atual: {field['text']}")

                for option in field["options"]:

                    marker = "*" if (
                        str(option["value"])
                        == str(field["value"])
                    ) else " "

                    print(
                        f"         {marker} "
                        f"{option['value']} = "
                        f"{option['text']}"
                    )

            elif field_type == "checkbox":

                state = "MARCADO" if field["checked"] else "DESMARCADO"

                print(f"CHECKBOX {name}")
                print(f"         estado: {state}")
                print(f"         value : {field['value']}")

            elif field_type == "radio":

                state = "SELECIONADO" if field["checked"] else ""

                print(f"RADIO    {name}")
                print(f"         value : {field['value']}")
                print(f"         {state}")

            else:

                print(
                    f"{field_type.upper():8} {name}"
                )

                print(
                    f"         valor atual: "
                    f"{field.get('value', '')}"
                )

        print()

    # ==========================================================
    # SET
    # ==========================================================

    def set_values(self, changes, dry_run=False):

        response = self.get()

        form = self.parse_form(response.text)

        print()
        print("=" * 70)
        print("PRINTER ASSISTANT")
        print("EWS GENERIC FORM EXECUTOR")
        print("=" * 70)

        print()
        print(f"Impressora : {self.printer_ip}")
        print(f"Página     : {self.page}")

        print()
        print("[1/5] Lendo formulário...")

        print(
            f"      ACTION : {form['action']}"
        )

        print(
            f"      METHOD : {form['method']}"
        )

        print(
            f"      CAMPOS : {len(form['fields'])}"
        )

        # ------------------------------------------------------
        # Descobrir estado atual
        # ------------------------------------------------------

        current = {}

        for field in form["fields"]:

            name = field["name"]

            if field["type"] == "checkbox":
                current[name] = (
                    "1" if field["checked"] else "0"
                )

            elif field["type"] == "radio":
                if field["checked"]:
                    current[name] = field["value"]

            else:
                current[name] = field.get(
                    "value",
                    ""
                )

        # ------------------------------------------------------
        # Preparar alterações
        # ------------------------------------------------------

        print()
        print("[2/5] Preparando alterações...")

        resolved_changes = {}

        for name, requested in changes.items():

            if name not in current:
                raise EWSCommandError(
                    f"Campo '{name}' não encontrado."
                )

            field = next(
                x for x in form["fields"]
                if x["name"] == name
            )

            old_value = current[name]

            if field["type"] == "select":

                new_value = self.resolve_select_value(
                    field,
                    requested
                )

                new_text = next(
                    x["text"]
                    for x in field["options"]
                    if str(x["value"])
                    == str(new_value)
                )

            elif field["type"] == "checkbox":

                new_value = (
                    "1"
                    if self.parse_bool(requested)
                    else "0"
                )

                new_text = (
                    "Marcado"
                    if new_value == "1"
                    else "Desmarcado"
                )

            else:

                new_value = str(requested)
                new_text = new_value

            resolved_changes[name] = new_value

            print()
            print(f"      CAMPO: {name}")
            print(f"      Tipo  : {field['type']}")
            print(f"      Antes : {old_value}")
            print(f"      Depois: {new_value}")
            print(f"      Pedido: {requested}")

            if field["type"] == "select":
                print(f"      Texto : {new_text}")

        # ------------------------------------------------------
        # DRY RUN
        # ------------------------------------------------------

        if dry_run:

            print()
            print("[DRY-RUN] Nenhuma alteração enviada.")

            payload = self.build_payload(
                form,
                resolved_changes
            )

            print()
            print("POST que seria enviado:")

            for name, value in payload:
                print(
                    f"      {name} = {value}"
                )

            return {
                "success": True,
                "dry_run": True,
                "changes": resolved_changes
            }

        # ------------------------------------------------------
        # Construir POST
        # ------------------------------------------------------

        payload = self.build_payload(
            form,
            resolved_changes
        )

        print()
        print("[3/5] Enviando POST...")

        response = self.post(
            form["action"],
            payload
        )

        print(
            f"      HTTP: {response.status_code}"
        )

        if response.status_code not in (200, 201, 202, 204):

            print(
                "      [ERRO] Impressora rejeitou a requisição."
            )

            raise EWSCommandError(
                f"POST retornou HTTP {response.status_code}"
            )

        print(
            "      [OK] Impressora aceitou a requisição."
        )

        # ------------------------------------------------------
        # Verificação
        # ------------------------------------------------------

        print()
        print("[4/5] Verificando estado...")

        verify_response = self.get()

        verify_form = self.parse_form(
            verify_response.text
        )

        verification = {}

        for name, expected_value in resolved_changes.items():

            field = next(
                (
                    x for x in verify_form["fields"]
                    if x["name"] == name
                ),
                None
            )

            if not field:
                verification[name] = {
                    "ok": False,
                    "error": "Campo desapareceu após POST"
                }
                continue

            # ----------------------------------------------
            # SELECT / TEXT / HIDDEN
            # ----------------------------------------------

            if field["type"] == "select":

                actual_value = field["value"]

                actual_text = field["text"]

                expected_text = next(
                    (
                        x["text"]
                        for x in field["options"]
                        if str(x["value"])
                        == str(expected_value)
                    ),
                    str(expected_value)
                )

            # ----------------------------------------------
            # CHECKBOX
            # ----------------------------------------------

            elif field["type"] == "checkbox":

                actual_value = (
                    "1"
                    if field["checked"]
                    else "0"
                )

                actual_text = (
                    "Marcado"
                    if field["checked"]
                    else "Desmarcado"
                )

                expected_text = (
                    "Marcado"
                    if expected_value == "1"
                    else "Desmarcado"
                )

            else:

                actual_value = field.get(
                    "value",
                    ""
                )

                actual_text = actual_value
                expected_text = expected_value

            ok = str(actual_value) == str(expected_value)

            verification[name] = {
                "ok": ok,
                "expected": expected_text,
                "expected_value": expected_value,
                "actual_value": actual_value,
                "actual_text": actual_text
            }

            print()
            print(f"      {'[OK]' if ok else '[ERRO]'} {name}")
            print(f"      Esperado: {expected_text}")
            print(f"      Atual   : {actual_value}")
            print(f"                {actual_text}")

        # ------------------------------------------------------
        # Resultado
        # ------------------------------------------------------

        success = all(
            item["ok"]
            for item in verification.values()
        )

        print()
        print("[5/5] Resultado")

        if success:
            print()
            print("[SUCESSO] Alterações confirmadas.")
        else:
            print()
            print(
                "[ERRO] Uma ou mais alterações "
                "não foram confirmadas."
            )

        return {
            "success": success,
            "dry_run": False,
            "changes": resolved_changes,
            "verification": verification
        }


# ==============================================================
# ARGUMENTOS
# ==============================================================

def parse_changes(values):

    changes = {}

    for item in values:

        if "=" not in item:
            raise EWSCommandError(
                f"Formato inválido: {item}"
            )

        name, value = item.split(
            "=",
            1
        )

        name = name.strip()
        value = value.strip()

        if not name:
            raise EWSCommandError(
                "Nome do campo vazio."
            )

        changes[name] = value

    return changes


def main():

    if len(sys.argv) < 3:

        print(
            "Uso:"
        )

        print(
            "  python -m tools.ews.command "
            "IP PAGINA --inspect"
        )

        print(
            "  python -m tools.ews.command "
            "IP PAGINA --set \"CAMPO=VALOR\""
        )

        print(
            "  python -m tools.ews.command "
            "IP PAGINA --set \"CAMPO=VALOR\" "
            "\"CAMPO2=VALOR2\""
        )

        print(
            "  python -m tools.ews.command "
            "IP PAGINA --set \"CAMPO=VALOR\" "
            "--dry-run"
        )

        sys.exit(1)

    printer_ip = sys.argv[1]
    page = sys.argv[2]

    inspect_mode = "--inspect" in sys.argv
    dry_run = "--dry-run" in sys.argv

    set_values = []

    i = 3

    while i < len(sys.argv):

        argument = sys.argv[i]

        if argument == "--set":

            i += 1

            while i < len(sys.argv):

                value = sys.argv[i]

                if value.startswith("--"):
                    i -= 1
                    break

                set_values.append(value)

                i += 1

        i += 1

    try:

        executor = EWSFormExecutor(
            printer_ip,
            page
        )

        if inspect_mode:

            executor.inspect()

            return

        if set_values:

            changes = parse_changes(
                set_values
            )

            result = executor.set_values(
                changes,
                dry_run=dry_run
            )

            print()
            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False
                )
            )

            if not result["success"]:
                sys.exit(2)

            return

        print(
            "Nenhuma operação especificada."
        )

        sys.exit(1)

    except EWSCommandError as e:

        print()
        print(
            f"[ERRO] {e}"
        )

        sys.exit(2)

    except requests.RequestException as e:

        print()
        print(
            f"[ERRO HTTP] {e}"
        )

        sys.exit(3)


if __name__ == "__main__":
    main()