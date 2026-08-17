# ews/form_engine.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class FieldOption:
    value: str
    text: str
    selected: bool = False


@dataclass
class FormField:
    name: str
    field_type: str
    value: str = ""
    checked: bool = False
    disabled: bool = False
    options: list[FieldOption] = field(default_factory=list)
    element: Any = None


@dataclass
class EWSForm:
    url: str
    action: str
    method: str
    fields: list[FormField]


class EWSFormEngine:
    """
    Executor genérico de formulários HTML do EWS.

    Responsabilidades:
      - GET da página
      - descobrir formulário
      - interpretar campos
      - resolver valores por texto ou valor
      - montar POST
      - enviar alteração
      - reler a página
      - verificar resultado
    """

    def __init__(
        self,
        printer_ip: str,
        timeout: int = 10,
        verify_ssl: bool = False,
    ):
        self.printer_ip = printer_ip
        self.base_url = f"http://{printer_ip}"

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": "PrinterAssistant-EWS/1.0",
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
            }
        )

        self.timeout = timeout
        self.verify_ssl = verify_ssl

    # ============================================================
    # URL
    # ============================================================

    def build_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://"):
            return path_or_url

        if path_or_url.startswith("https://"):
            return path_or_url

        if not path_or_url.startswith("/"):
            path_or_url = "/" + path_or_url

        return urljoin(self.base_url + "/", path_or_url.lstrip("/"))

    # ============================================================
    # HTTP
    # ============================================================

    def get(self, path_or_url: str) -> requests.Response:
        url = self.build_url(path_or_url)

        response = self.session.get(
            url,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )

        response.raise_for_status()

        return response

    def post(
        self,
        url: str,
        data: list[tuple[str, str]],
    ) -> requests.Response:

        response = self.session.post(
            url,
            data=data,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )

        response.raise_for_status()

        return response

    # ============================================================
    # ENCODING
    # ============================================================

    def decode_response(self, response: requests.Response) -> str:
        """
        Alguns EWS antigos informam charset errado.
        Por isso não confiamos cegamente em response.text.
        """

        content = response.content

        # UTF-8 é a primeira tentativa.
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            pass

        # ISO-8859-1 nunca falha.
        return content.decode("iso-8859-1", errors="replace")

    # ============================================================
    # PARSE
    # ============================================================

    def parse_form(
        self,
        path_or_url: str,
        html: Optional[str] = None,
    ) -> EWSForm:

        url = self.build_url(path_or_url)

        if html is None:
            response = self.get(url)
            html = self.decode_response(response)

        soup = BeautifulSoup(html, "html.parser")

        form = soup.find("form")

        if form is None:
            raise RuntimeError(
                f"Nenhum <form> encontrado em {url}"
            )

        action = form.get("action", "").strip()

        if action:
            action = urljoin(url, action)
        else:
            action = url

        method = form.get("method", "GET").upper()

        fields: list[FormField] = []

        # --------------------------------------------------------
        # INPUT
        # --------------------------------------------------------

        for element in form.find_all("input"):

            name = element.get("name")

            if not name:
                continue

            field_type = element.get("type", "text").lower()

            disabled = element.has_attr("disabled")

            value = element.get("value", "")

            checked = element.has_attr("checked")

            field = FormField(
                name=name,
                field_type=field_type,
                value=value,
                checked=checked,
                disabled=disabled,
                element=element,
            )

            fields.append(field)

        # --------------------------------------------------------
        # SELECT
        # --------------------------------------------------------

        for element in form.find_all("select"):

            name = element.get("name")

            if not name:
                continue

            disabled = element.has_attr("disabled")

            options: list[FieldOption] = []

            selected_value = ""

            for option in element.find_all("option"):

                value = option.get("value", "")
                text = option.get_text(" ", strip=True)

                selected = option.has_attr("selected")

                if selected:
                    selected_value = value

                options.append(
                    FieldOption(
                        value=value,
                        text=text,
                        selected=selected,
                    )
                )

            # Alguns EWS não marcam explicitamente selected.
            if not selected_value and options:
                selected_value = options[0].value

            field = FormField(
                name=name,
                field_type="select",
                value=selected_value,
                disabled=disabled,
                options=options,
                element=element,
            )

            fields.append(field)

        # --------------------------------------------------------
        # TEXTAREA
        # --------------------------------------------------------

        for element in form.find_all("textarea"):

            name = element.get("name")

            if not name:
                continue

            value = element.get_text()

            fields.append(
                FormField(
                    name=name,
                    field_type="textarea",
                    value=value,
                    disabled=element.has_attr("disabled"),
                    element=element,
                )
            )

        return EWSForm(
            url=url,
            action=action,
            method=method,
            fields=fields,
        )

    # ============================================================
    # FIND FIELD
    # ============================================================

    def find_field(
        self,
        form: EWSForm,
        name: str,
    ) -> FormField:

        for field in form.fields:
            if field.name == name:
                return field

        raise KeyError(
            f"Campo não encontrado: {name}"
        )

    # ============================================================
    # DISPLAY
    # ============================================================

    def selected_option(
        self,
        field: FormField,
    ) -> Optional[FieldOption]:

        if field.field_type != "select":
            return None

        for option in field.options:
            if option.value == field.value:
                return option

        return None

    def field_text(
        self,
        field: FormField,
    ) -> str:

        if field.field_type == "select":

            option = self.selected_option(field)

            if option:
                return option.text

        if field.field_type in ("checkbox", "radio"):
            return "marcado" if field.checked else "desmarcado"

        return field.value

    # ============================================================
    # RESOLVE SELECT
    # ============================================================

    def resolve_select_value(
        self,
        field: FormField,
        requested: str,
    ) -> str:

        requested = str(requested).strip()

        # Primeiro: valor exato.
        for option in field.options:

            if option.value == requested:
                return option.value

        # Segundo: texto exato, ignorando maiúsculas/minúsculas.
        for option in field.options:

            if option.text.strip().lower() == requested.lower():
                return option.value

        # Terceiro: comparação simplificada.
        normalized = requested.casefold()

        for option in field.options:

            if option.text.strip().casefold() == normalized:
                return option.value

        available = ", ".join(
            f"{o.value}={o.text}"
            for o in field.options
        )

        raise ValueError(
            f"Valor '{requested}' não encontrado "
            f"para {field.name}. "
            f"Opções: {available}"
        )

    # ============================================================
    # APPLY CHANGE
    # ============================================================

    def apply_change(
        self,
        field: FormField,
        requested: str,
    ) -> dict:

        old_value = field.value
        old_text = self.field_text(field)

        requested = str(requested)

        # --------------------------------------------------------
        # SELECT
        # --------------------------------------------------------

        if field.field_type == "select":

            new_value = self.resolve_select_value(
                field,
                requested,
            )

            field.value = new_value

            new_text = self.field_text(field)

        # --------------------------------------------------------
        # CHECKBOX
        # --------------------------------------------------------

        elif field.field_type == "checkbox":

            value = requested.strip().lower()

            true_values = {
                "1",
                "true",
                "yes",
                "on",
                "sim",
                "marcado",
                "ativado",
                "ativar",
            }

            false_values = {
                "0",
                "false",
                "no",
                "off",
                "nao",
                "não",
                "desmarcado",
                "desativado",
                "desativar",
            }

            if value in true_values:
                field.checked = True

            elif value in false_values:
                field.checked = False

            else:
                raise ValueError(
                    f"Valor inválido para checkbox "
                    f"{field.name}: {requested}"
                )

            new_value = (
                field.value
                if field.checked
                else ""
            )

            new_text = (
                "marcado"
                if field.checked
                else "desmarcado"
            )

        # --------------------------------------------------------
        # RADIO
        # --------------------------------------------------------

        elif field.field_type == "radio":

            if requested == field.value:
                field.checked = True

            elif requested.lower() in {
                "true",
                "1",
                "on",
                "sim",
            }:
                field.checked = True

            elif requested.lower() in {
                "false",
                "0",
                "off",
                "nao",
                "não",
            }:
                field.checked = False

            else:
                raise ValueError(
                    f"Valor inválido para radio "
                    f"{field.name}: {requested}"
                )

            new_value = field.value

            new_text = (
                "marcado"
                if field.checked
                else "desmarcado"
            )

        # --------------------------------------------------------
        # TEXT / TEXTAREA / HIDDEN
        # --------------------------------------------------------

        else:

            field.value = requested

            new_value = requested
            new_text = requested

        return {
            "old_value": old_value,
            "new_value": new_value,
            "old_text": old_text,
            "requested": requested,
            "new_text": new_text,
        }

    # ============================================================
    # BUILD POST DATA
    # ============================================================

    def build_post_data(
        self,
        form: EWSForm,
    ) -> list[tuple[str, str]]:

        data: list[tuple[str, str]] = []

        for field in form.fields:

            if field.disabled:
                continue

            # ----------------------------------------------------
            # SELECT
            # ----------------------------------------------------

            if field.field_type == "select":

                data.append(
                    (
                        field.name,
                        field.value,
                    )
                )

            # ----------------------------------------------------
            # CHECKBOX
            # ----------------------------------------------------

            elif field.field_type == "checkbox":

                # HTML só envia checkbox marcado.
                if field.checked:

                    data.append(
                        (
                            field.name,
                            field.value or "on",
                        )
                    )

            # ----------------------------------------------------
            # RADIO
            # ----------------------------------------------------

            elif field.field_type == "radio":

                if field.checked:

                    data.append(
                        (
                            field.name,
                            field.value,
                        )
                    )

            # ----------------------------------------------------
            # BUTTON
            # ----------------------------------------------------

            elif field.field_type in {
                "submit",
                "reset",
                "button",
                "image",
            }:

                continue

            # ----------------------------------------------------
            # OUTROS
            # ----------------------------------------------------

            else:

                data.append(
                    (
                        field.name,
                        field.value,
                    )
                )

        return data

    # ============================================================
    # INSPECT
    # ============================================================

    def inspect(
        self,
        form: EWSForm,
    ) -> None:

        print()
        print("=" * 70)
        print("EWS FORM INSPECTOR")
        print("=" * 70)

        print()
        print(f"URL    : {form.url}")
        print(f"ACTION : {form.action}")
        print(f"METHOD : {form.method}")
        print(f"CAMPOS : {len(form.fields)}")

        print()

        for field in form.fields:

            print(
                f"{field.field_type.upper():8} "
                f"{field.name}"
            )

            if field.field_type == "select":

                print(
                    f"         valor atual: {field.value}"
                )

                print(
                    f"         texto atual: "
                    f"{self.field_text(field)}"
                )

                for option in field.options:

                    marker = "* " if (
                        option.value == field.value
                    ) else "  "

                    print(
                        f"         {marker}"
                        f"{option.value:>4} = "
                        f"{option.text}"
                    )

            elif field.field_type in {
                "checkbox",
                "radio",
            }:

                print(
                    f"         valor: {field.value}"
                )

                print(
                    f"         estado: "
                    f"{'marcado' if field.checked else 'desmarcado'}"
                )

            else:

                print(
                    f"         valor: {field.value}"
                )

            print()

    # ============================================================
    # CHANGE
    # ============================================================

    def change(
        self,
        path_or_url: str,
        changes: dict[str, str],
        dry_run: bool = False,
    ) -> dict:

        # --------------------------------------------------------
        # 1. GET
        # --------------------------------------------------------

        response = self.get(path_or_url)

        html = self.decode_response(response)

        form = self.parse_form(
            path_or_url,
            html=html,
        )

        # --------------------------------------------------------
        # 2. APPLY
        # --------------------------------------------------------

        result_changes = {}

        print()
        print("=" * 70)
        print("EWS GENERIC COMMAND ENGINE")
        print("=" * 70)

        print()
        print(f"Impressora : {self.printer_ip}")
        print(f"Página     : {path_or_url}")

        print()
        print("[1/4] Lendo formulário...")

        print(
            f"      ACTION : {form.action}"
        )

        print(
            f"      METHOD : {form.method}"
        )

        print(
            f"      CAMPOS : {len(form.fields)}"
        )

        print()
        print("[2/4] Preparando alteração...")

        for name, requested in changes.items():

            field = self.find_field(
                form,
                name,
            )

            before = self.field_text(field)

            change_info = self.apply_change(
                field,
                requested,
            )

            result_changes[name] = change_info

            print()
            print(f"      CAMPO: {name}")
            print(
                f"      Antes : {change_info['old_value']}"
            )
            print(
                f"              {change_info['old_text']}"
            )
            print(
                f"      Depois: {change_info['new_value']}"
            )
            print(
                f"      Pedido: {requested}"
            )

        # --------------------------------------------------------
        # DRY RUN
        # --------------------------------------------------------

        if dry_run:

            print()
            print("[DRY-RUN] Nenhuma alteração enviada.")

            return {
                "success": True,
                "dry_run": True,
                "changes": result_changes,
            }

        # --------------------------------------------------------
        # 3. POST
        # --------------------------------------------------------

        post_data = self.build_post_data(form)

        print()
        print("[3/4] Enviando POST...")

        post_response = self.post(
            form.action,
            post_data,
        )

        print(
            f"      HTTP: {post_response.status_code}"
        )

        print(
            "      [OK] Impressora aceitou a requisição."
        )

        # --------------------------------------------------------
        # 4. VERIFY
        # --------------------------------------------------------

        print()
        print("[4/4] Verificando estado...")

        verification = {}

        verify_response = self.get(path_or_url)

        verify_html = self.decode_response(
            verify_response
        )

        verify_form = self.parse_form(
            path_or_url,
            html=verify_html,
        )

        all_ok = True

        for name, requested in changes.items():

            original_field = self.find_field(
                form,
                name,
            )

            verify_field = self.find_field(
                verify_form,
                name,
            )

            if verify_field.field_type == "select":

                expected_value = self.resolve_select_value(
                    original_field,
                    requested,
                )

                actual_value = verify_field.value

                expected_text = next(
                    (
                        option.text
                        for option in original_field.options
                        if option.value == expected_value
                    ),
                    requested,
                )

                actual_text = self.field_text(
                    verify_field
                )

                ok = actual_value == expected_value

            elif verify_field.field_type == "checkbox":

                requested_lower = requested.strip().lower()

                expected_checked = requested_lower in {
                    "1",
                    "true",
                    "yes",
                    "on",
                    "sim",
                    "marcado",
                    "ativado",
                    "ativar",
                }

                ok = (
                    verify_field.checked
                    == expected_checked
                )

                expected_value = (
                    "1"
                    if expected_checked
                    else "0"
                )

                actual_value = (
                    "1"
                    if verify_field.checked
                    else "0"
                )

                expected_text = (
                    "marcado"
                    if expected_checked
                    else "desmarcado"
                )

                actual_text = (
                    "marcado"
                    if verify_field.checked
                    else "desmarcado"
                )

            else:

                expected_value = requested
                actual_value = verify_field.value

                expected_text = requested
                actual_text = verify_field.value

                ok = actual_value == expected_value

            verification[name] = {
                "ok": ok,
                "expected": expected_text,
                "expected_value": expected_value,
                "actual_value": actual_value,
                "actual_text": actual_text,
            }

            print()
            print(f"      {'[OK]' if ok else '[ERRO]'} {name}")
            print(
                f"      Esperado: {expected_text}"
            )
            print(
                f"      Atual   : {actual_value}"
            )
            print(
                f"                {actual_text}"
            )

            if not ok:
                all_ok = False

        print()

        if all_ok:

            print(
                "[SUCESSO] Alteração confirmada."
            )

        else:

            print(
                "[FALHA] POST aceito, mas "
                "a verificação não confirmou todas as alterações."
            )

        return {
            "success": all_ok,
            "dry_run": False,
            "changes": result_changes,
            "verification": verification,
        }