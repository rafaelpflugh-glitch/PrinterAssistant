import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)

from core.capability_registry import CapabilityRegistry


def load_json(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def import_ews_map(printer_ip, map_file):

    data = load_json(map_file)

    registry = CapabilityRegistry(
        printer_ip
    )

    pages = data.get("pages", [])

    imported = 0

    for page in pages:

        url = page.get("url", "")
        forms = page.get("forms", [])

        for form in forms:

            action = form.get("action")
            method = form.get(
                "method",
                "GET"
            )

            for field in form.get(
                "fields",
                []
            ):

                field_type = field.get(
                    "type"
                )

                name = field.get(
                    "name"
                )

                if not name:
                    continue

                values = field.get(
                    "options"
                )

                registry.register(

                    name=name,

                    category="EWS",

                    source="EWS",

                    endpoint=url,

                    parameter=name,

                    values=values,

                    status="DISCOVERED",

                    evidence={
                        "method": method,
                        "action": action,
                        "field_type": field_type
                    }
                )

                imported += 1

    registry.save()

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT")
    print("EWS → CAPABILITY REGISTRY")
    print("=" * 70)
    print()
    print(f"Impressora : {printer_ip}")
    print(f"Páginas    : {len(pages)}")
    print(f"Campos     : {imported}")
    print()
    print("Registry:")
    print(registry.path)
    print()
    print("Categorias:")

    for category, count in registry.summary().items():
        print(
            f"  {category:<15} {count}"
        )


if __name__ == "__main__":

    if len(sys.argv) != 3:

        print(
            "Uso:"
        )

        print(
            "python tools\\discovery\\ews_import.py "
            "IP MAPA.json"
        )

        sys.exit(1)

    import_ews_map(
        sys.argv[1],
        sys.argv[2]
    )