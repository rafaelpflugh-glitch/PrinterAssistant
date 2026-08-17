import sys
from pathlib import Path

# ============================================================
# IMPORTANTE:
# permite importar "ews" mesmo executando o script dentro
# da pasta tools.
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from ews.discovery import EWSDiscovery


def main():

    if len(sys.argv) < 2:

        print(
            "Uso:"
        )

        print(
            "python tools\\ews_discover_v2.py "
            "<IP> [CAMINHO]"
        )

        print()

        print(
            "Exemplo:"
        )

        print(
            "python tools\\ews_discover_v2.py "
            "192.168.14.134 "
            "/cgi-bin/dynamic/printer/config/gen/papermenu.html"
        )

        return

    printer_ip = sys.argv[1]

    start_path = (
        sys.argv[2]
        if len(sys.argv) >= 3
        else "/"
    )

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT")
    print("EWS DISCOVERY ENGINE v2")
    print("=" * 70)
    print()
    print(f"Impressora : {printer_ip}")
    print(f"Início     : {start_path}")
    print()
    print("Iniciando descoberta...")
    print()

    scanner = EWSDiscovery(
        printer_ip=printer_ip,
        output_dir="ews",
        max_pages=500,
    )

    pages = scanner.crawl(
        start_path
    )

    map_path, knowledge_path = (
        scanner.save_results()
    )

    print()
    print("=" * 70)
    print("DISCOVERY FINALIZADO")
    print("=" * 70)
    print()
    print(
        f"Páginas descobertas : {len(pages)}"
    )

    forms = sum(
        len(page.forms)
        for page in pages
    )

    fields = sum(
        len(form.fields)
        for page in pages
        for form in page.forms
    )

    print(
        f"Formulários          : {forms}"
    )

    print(
        f"Campos               : {fields}"
    )

    print()
    print(
        f"Mapa bruto:"
    )
    print(
        f"  {map_path}"
    )

    print()
    print(
        f"Knowledge Map:"
    )
    print(
        f"  {knowledge_path}"
    )

    print()


if __name__ == "__main__":
    main()