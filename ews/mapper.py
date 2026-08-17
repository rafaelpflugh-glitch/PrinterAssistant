import json
import re
from pathlib import Path

from .model import Page, Form, Field, Command


# ============================================================
# CLASSIFICAÇÃO SEMÂNTICA
# ============================================================

CATEGORY_RULES = {
    "paper": [
        "paper",
        "papel",
        "paperweight",
        "papertexture",
        "paperload",
        "papermenu",
        "customtype",
        "customname",
        "customscan",
        "universal",
        "uni_width",
        "uni_height",
    ],

    "print": [
        "print",
        "impress",
        "duplex",
        "resolution",
        "resolução",
        "copies",
        "cópias",
    ],

    "scan": [
        "scan",
        "scanner",
        "scanning",
        "digital",
        "digitaliz",
        "aad",
        "adf",
    ],

    "copy": [
        "copy",
        "cópia",
        "copiar",
    ],

    "network": [
        "network",
        "rede",
        "tcp",
        "ip",
        "ipv4",
        "ipv6",
        "dns",
        "gateway",
        "dhcp",
        "ethernet",
        "wifi",
        "wireless",
        "snmp",
    ],

    "security": [
        "security",
        "segurança",
        "password",
        "senha",
        "user",
        "usuário",
        "authentication",
        "autenticação",
    ],

    "maintenance": [
        "maintenance",
        "manutenção",
        "clean",
        "limpeza",
        "calibration",
        "calibração",
        "reset",
        "substit",
    ],

    "supplies": [
        "supply",
        "suprimento",
        "toner",
        "cartucho",
        "drum",
        "fotocondutor",
        "imaging",
    ],

    "status": [
        "status",
        "state",
        "estado",
        "information",
        "informação",
        "device",
        "printer",
        "impressora",
    ],
}


# ============================================================
# UTILIDADES
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }

    for a, b in replacements.items():
        text = text.replace(a, b)

    return text


def classify_category(page_url, field):
    text = " ".join([
        page_url or "",
        field.name or "",
        field.field_id or "",
        field.text or "",
    ])

    text = normalize(text)

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if normalize(keyword) in text:
                return category

    return "unknown"


def semantic_description(field):
    if field.text:
        return field.text.strip()

    if field.name:
        return field.name

    if field.field_id:
        return field.field_id

    return "Campo EWS"


def extract_system_id(name):
    if not name:
        return None

    match = re.search(r"(?:0|1|2)\.system\.(\d+)", name)

    if match:
        return match.group(1)

    return None


# ============================================================
# COMMAND GENERATOR
# ============================================================

def generate_commands(pages):
    commands = []

    counter = 1

    for page in pages:
        for form in page.forms:

            for field in form.fields:

                if not field.name:
                    continue

                # Campos que realmente podem gerar uma ação
                if field.field_type not in (
                    "select",
                    "text",
                    "number",
                    "checkbox",
                    "radio",
                    "hidden",
                ):
                    continue

                category = classify_category(page.url, field)

                system_id = extract_system_id(field.name)

                if system_id:
                    command_id = f"{category}.system.{system_id}"
                else:
                    command_id = f"{category}.field.{counter}"

                options = {}

                for option in field.options:
                    options[str(option.value)] = option.text

                command = {
                    "command_id": command_id,
                    "category": category,
                    "description": semantic_description(field),
                    "page_url": page.url,
                    "action": form.action,
                    "method": form.method,
                    "field_name": field.name,
                    "field_type": field.field_type,
                    "current_value": field.value,
                    "options": options,
                }

                commands.append(command)

                counter += 1

    return commands


# ============================================================
# CONSTRUÇÃO DO KNOWLEDGE MAP
# ============================================================

def build_knowledge(pages):
    commands = generate_commands(pages)

    knowledge = {
        "version": 1,
        "pages": [],
        "commands": commands,
        "statistics": {
            "pages": len(pages),
            "forms": 0,
            "fields": 0,
            "commands": len(commands),
            "categories": {},
        },
    }

    for page in pages:

        page_data = {
            "url": page.url,
            "status": page.status,
            "bytes": page.bytes,
            "title": page.title,
            "links": page.links,
            "forms": [],
        }

        for form in page.forms:

            knowledge["statistics"]["forms"] += 1

            form_data = {
                "action": form.action,
                "method": form.method,
                "fields": [],
            }

            for field in form.fields:

                knowledge["statistics"]["fields"] += 1

                field_data = {
                    "type": field.field_type,
                    "name": field.name,
                    "id": field.field_id,
                    "value": field.value,
                    "text": field.text,
                    "options": [
                        {
                            "value": option.value,
                            "text": option.text,
                            "selected": option.selected,
                        }
                        for option in field.options
                    ],
                }

                form_data["fields"].append(field_data)

            page_data["forms"].append(form_data)

        knowledge["pages"].append(page_data)

    # Estatísticas por categoria

    for command in commands:

        category = command["category"]

        knowledge["statistics"]["categories"][category] = (
            knowledge["statistics"]["categories"].get(category, 0) + 1
        )

    return knowledge


def save_knowledge(knowledge, path):

    path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            knowledge,
            f,
            indent=2,
            ensure_ascii=False,
        )


def load_knowledge(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)