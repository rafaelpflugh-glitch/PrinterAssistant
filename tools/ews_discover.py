import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ews.engine import CommandEngine, print_discovery


def main():

    if len(sys.argv) < 3:
        print()
        print("Uso:")
        print()
        print(
            "python tools\\ews_discover.py "
            "IP CAMINHO_EWS"
        )
        print()
        print("Exemplo:")
        print(
            "python tools\\ews_discover.py "
            "192.168.14.134 "
            "/cgi-bin/dynamic/printer/config/paper/paperweight.html"
        )
        print()
        return

    ip = sys.argv[1]
    path = sys.argv[2]

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT")
    print("EWS DEEP DISCOVERY")
    print("=" * 70)
    print()
    print("Impressora:", ip)
    print("Página    :", path)
    print()
    print("Lendo EWS...")
    print()

    engine = CommandEngine(ip)

    try:
        discovery = engine.discover_page(path)

    except Exception as e:
        print()
        print("[ERRO]")
        print(e)
        return

    print_discovery(discovery)

    safe_name = (
        path
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    if safe_name.endswith(".html"):
        safe_name = safe_name[:-5]

    output = engine.save_discovery(
        safe_name,
        discovery
    )

    print()
    print("=" * 70)
    print("MAPA SALVO")
    print("=" * 70)
    print()
    print(output)
    print()


if __name__ == "__main__":
    main()