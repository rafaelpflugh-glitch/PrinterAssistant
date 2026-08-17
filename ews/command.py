# ============================================================
# PRINTER ASSISTANT
# EWS GENERIC COMMAND ENGINE
# ============================================================

from __future__ import annotations

import json
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
    options: list[FieldOption] = field(default_factory=list)

    @property
    def current_text(self) -> Optional[str]:
        for option in self.options:
            if option.selected:
                return option.text
        return None


@dataclass
class EWSForm:
    page_url: str
    action: str
    method: str
    fields: list[FormField]


class EWSCommandError(Exception):
    pass


class EWSCommandEngine:

    def __init__(
        self,
        printer_ip: str,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
    ):
        self.printer_ip = printer_ip
        self.base_url = f"http://{printer_ip}/"
        self.timeout = timeout

        self.session = session or requests.Session()

        self.session.headers.update({
            "User-Agent": "PrinterAssistant/1.0 EWSCommandEngine"
        })

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    def make_url(self, path: str) -> str:

        if path.startswith("http://") or path.startswith("https://"):
            return path

        if not path.startswith("/"):
            path = "/" + path

        return urljoin(self.base_url, path)

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def get_page(self, path: str):

        url = self.make_url(path)

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response

    # --------------------------------------------------------
    # PARSE FORM
    # --------------------------------------------------------

    def parse_form(self, html: str, page_url: str) -> EWSForm:

        soup = BeautifulSoup(html, "html.parser")

        form = soup.find("form")

        if form is None:
            raise EWSCommandError(
                f"Nenhum formulário encontrado em {page_url}"
            )

        action = form.get("action") or page_url

        action = urljoin(
            page_url,
            action
        )

        method = (
            form.get("method")
            or "GET"
        ).upper()

        fields: list[FormField] = []

        # ----------------------------------------------------
        # SELECT
        # ----------------------------------------------------

        for element in form.find_all("select"):

            name = element.get("name")

            if not name:
                continue

            options = []

            for option in element.find_all("option"):

                value = option.get("value", "")

                text = option.get_text(
                    " ",
                    strip=True
                )

                selected = option.has_attr("selected")

                options.append(
                    FieldOption(
                        value=value,
                        text=text,
                        selected=selected,
                    )
                )

            current_value = ""

            selected = next(
                (
                    x
                    for x in options
                    if x.selected
                ),
                None
            )

            if selected:
                current_value = selected.value

            fields.append(
                FormField(
                    name=name,
                    field_type="select",
                    value=current_value,
                    options=options,
                )
            )

        # ----------------------------------------------------
        # INPUTS
        # ----------------------------------------------------

        for element in form.find_all("input"):

            input_type = (
                element.get("type")
                or "text"
            ).lower()

            name = element.get("name")

            if not name:
                continue

            # submit/reset não representam configuração
            if input_type in {
                "submit",
                "reset",
                "button",
            }:
                continue

            value = element.get(
                "value",
                ""
            )

            # checkbox
            if input_type == "checkbox":

                if element.has_attr("checked"):
                    value = value or "1"
                else:
                    value = ""

            fields.append(
                FormField(
                    name=name,
                    field_type=input_type,
                    value=value,
                )
            )

        return EWSForm(
            page_url=page_url,
            action=action,
            method=method,
            fields=fields,
        )

    # --------------------------------------------------------
    # READ FORM
    # --------------------------------------------------------

    def read_form(self, path: str) -> EWSForm:

        response = self.get_page(path)

        url = response.url

        return self.parse_form(
            response.text,
            url,
        )

    # --------------------------------------------------------
    # FORM -> DICT
    # --------------------------------------------------------

    def form_to_dict(
        self,
        form: EWSForm,
    ) -> dict[str, str]:

        data = {}

        for field in form.fields:

            if field.field_type == "checkbox":

                if field.value:
                    data[field.name] = field.value

                continue

            data[field.name] = field.value

        return data

    # --------------------------------------------------------
    # FIND FIELD
    # --------------------------------------------------------

    def find_field(
        self,
        form: EWSForm,
        field_name: str,
    ) -> FormField:

        for field in form.fields:

            if field.name == field_name:
                return field

        raise EWSCommandError(
            f"Campo não encontrado: {field_name}"
        )

    # --------------------------------------------------------
    # RESOLVE VALUE
    # --------------------------------------------------------

    def resolve_value(
        self,
        field: FormField,
        desired: Any,
    ) -> str:

        desired_string = str(desired)

        # ----------------------------------------------------
        # SELECT
        # ----------------------------------------------------

        if field.field_type == "select":

            # Primeiro tenta valor exato
            for option in field.options:

                if option.value == desired_string:
                    return option.value

            # Depois tenta texto exato
            for option in field.options:

                if (
                    option.text.strip().lower()
                    == desired_string.strip().lower()
                ):
                    return option.value

            # Depois tenta texto contendo
            for option in field.options:

                if (
                    desired_string.strip().lower()
                    in option.text.strip().lower()
                ):
                    return option.value

            available = ", ".join(
                f"{x.value}={x.text}"
                for x in field.options
            )

            raise EWSCommandError(
                f"Valor '{desired}' não encontrado "
                f"para {field.name}. "
                f"Disponíveis: {available}"
            )

        # ----------------------------------------------------
        # TEXT / HIDDEN / ETC
        # ----------------------------------------------------

        return desired_string

    # --------------------------------------------------------
    # APPLY CHANGES
    # --------------------------------------------------------

    def prepare_data(
        self,
        form: EWSForm,
        changes: dict[str, Any],
    ) -> tuple[dict[str, str], dict[str, Any]]:

        data = self.form_to_dict(form)

        applied = {}

        for field_name, desired in changes.items():

            field = self.find_field(
                form,
                field_name,
            )

            old_value = field.value

            new_value = self.resolve_value(
                field,
                desired,
            )

            data[field_name] = new_value

            applied[field_name] = {
                "old_value": old_value,
                "new_value": new_value,
                "old_text": field.current_text,
                "requested": desired,
            }

        return data, applied

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    def submit(
        self,
        form: EWSForm,
        data: dict[str, str],
    ):

        if form.method != "POST":

            raise EWSCommandError(
                f"Formulário não é POST: {form.method}"
            )

        response = self.session.post(
            form.action,
            data=data,
            timeout=self.timeout,
        )

        return response

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    def verify(
        self,
        path: str,
        expected: dict[str, Any],
    ):

        form = self.read_form(path)

        results = {}

        for field_name, desired in expected.items():

            field = self.find_field(
                form,
                field_name,
            )

            actual_value = field.value

            if field.field_type == "select":

                actual_text = field.current_text

                desired_value = self.resolve_value(
                    field,
                    desired,
                )

                ok = actual_value == desired_value

            else:

                actual_text = None
                desired_value = str(desired)

                ok = actual_value == desired_value

            results[field_name] = {
                "ok": ok,
                "expected": desired,
                "expected_value": desired_value,
                "actual_value": actual_value,
                "actual_text": actual_text,
            }

        return results

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    def execute(
        self,
        path: str,
        changes: dict[str, Any],
        verify: bool = True,
        dry_run: bool = False,
    ):

        print()
        print("=" * 70)
        print("PRINTER ASSISTANT")
        print("EWS GENERIC COMMAND ENGINE")
        print("=" * 70)

        print()
        print(f"Impressora : {self.printer_ip}")
        print(f"Página     : {path}")

        # ----------------------------------------------------
        # READ
        # ----------------------------------------------------

        print()
        print("[1/4] Lendo formulário...")

        form = self.read_form(path)

        print(
            f"      ACTION : {form.action}"
        )

        print(
            f"      METHOD : {form.method}"
        )

        print(
            f"      CAMPOS : {len(form.fields)}"
        )

        # ----------------------------------------------------
        # PREPARE
        # ----------------------------------------------------

        print()
        print("[2/4] Preparando alteração...")

        data, applied = self.prepare_data(
            form,
            changes,
        )

        for name, info in applied.items():

            print()
            print(f"      CAMPO: {name}")

            print(
                f"      Antes : "
                f"{info['old_value']}"
            )

            if info["old_text"] is not None:
                print(
                    f"              "
                    f"{info['old_text']}"
                )

            print(
                f"      Depois: "
                f"{info['new_value']}"
            )

            print(
                f"      Pedido: "
                f"{info['requested']}"
            )

        # ----------------------------------------------------
        # DRY RUN
        # ----------------------------------------------------

        if dry_run:

            print()
            print("[DRY-RUN]")
            print(
                "      Nenhuma alteração enviada."
            )

            return {
                "success": True,
                "dry_run": True,
                "changes": applied,
            }

        # ----------------------------------------------------
        # POST
        # ----------------------------------------------------

        print()
        print("[3/4] Enviando POST...")

        response = self.submit(
            form,
            data,
        )

        print(
            f"      HTTP: {response.status_code}"
        )

        if not response.ok:

            raise EWSCommandError(
                f"POST falhou: "
                f"HTTP {response.status_code}"
            )

        print(
            "      [OK] Impressora aceitou a requisição."
        )

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        verification = None

        if verify:

            print()
            print("[4/4] Verificando estado...")

            verification = self.verify(
                path,
                changes,
            )

            all_ok = True

            for name, result in verification.items():

                status = (
                    "OK"
                    if result["ok"]
                    else "FALHOU"
                )

                print()
                print(
                    f"      [{status}] {name}"
                )

                print(
                    f"      Esperado: "
                    f"{result['expected']}"
                )

                print(
                    f"      Atual   : "
                    f"{result['actual_value']}"
                )

                if result["actual_text"]:

                    print(
                        f"                "
                        f"{result['actual_text']}"
                    )

                if not result["ok"]:
                    all_ok = False

            print()

            if all_ok:

                print(
                    "[SUCESSO] Alteração confirmada."
                )

            else:

                print(
                    "[ATENÇÃO] POST aceito, "
                    "mas a verificação não confirmou "
                    "todos os valores."
                )

        return {
            "success": True,
            "dry_run": False,
            "changes": applied,
            "verification": verification,
        }


# ============================================================
# UTILITÁRIOS
# ============================================================

def print_form(
    engine: EWSCommandEngine,
    path: str,
):

    form = engine.read_form(path)

    print()
    print("=" * 70)
    print("EWS FORM INSPECTOR")
    print("=" * 70)

    print()
    print(f"URL    : {form.page_url}")
    print(f"ACTION : {form.action}")
    print(f"METHOD : {form.method}")
    print(f"CAMPOS : {len(form.fields)}")

    for field in form.fields:

        print()
        print(
            f"{field.field_type.upper():8} "
            f"{field.name}"
        )

        print(
            f"         valor atual: "
            f"{field.value}"
        )

        if field.current_text:

            print(
                f"         texto atual: "
                f"{field.current_text}"
            )

        if field.options:

            for option in field.options:

                marker = (
                    "*"
                    if option.selected
                    else " "
                )

                print(
                    f"         {marker} "
                    f"{option.value:>4} = "
                    f"{option.text}"
                )


def save_result(
    path: str,
    result: dict,
):

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )