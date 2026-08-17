from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from urllib.parse import urlparse


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DEFAULT_CAPABILITIES_DIR = os.path.join(
    BASE_DIR,
    "ews",
    "capabilities"
)

DEFAULT_OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "ews",
    "capabilities"
)


def normalize_url(url: str) -> str:
    """
    Remove diferenças artificiais de URL para permitir deduplicação.
    """
    if not url:
        return url

    url = url.strip()

    if url.endswith("/"):
        url = url[:-1]

    return url


def is_posttest(url: str) -> bool:
    """
    Identifica URLs usadas pelo EWS como destino POST.
    """
    path = urlparse(url).path.lower()

    return (
        "/cgi-bin/posttest/" in path
        or "/posttest/" in path
    )


def real_page_from_posttest(url: str) -> str:
    """
    Converte:

        /cgi-bin/posttest/printer/config/...

    para:

        /cgi-bin/dynamic/printer/config/...

    Isso representa a página que contém o formulário.
    """

    parsed = urlparse(url)

    path = parsed.path

    path = path.replace(
        "/cgi-bin/posttest/",
        "/cgi-bin/dynamic/",
        1
    )

    result = parsed._replace(
        path=path,
        query="",
        fragment=""
    )

    return result.geturl()


def load_json(path: str):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_json(path: str, data):
    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def find_capability_map(ip: str, explicit_map: str | None):
    if explicit_map:
        if not os.path.exists(explicit_map):
            raise FileNotFoundError(
                f"Mapa não encontrado: {explicit_map}"
            )

        return explicit_map

    safe_ip = ip.replace(".", "_")

    candidates = [
        os.path.join(
            DEFAULT_CAPABILITIES_DIR,
            f"capabilities_{ip}.json"
        ),
        os.path.join(
            DEFAULT_CAPABILITIES_DIR,
            f"capabilities_{safe_ip}.json"
        ),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(
        "Nenhum Capability Map encontrado.\n"
        + "\n".join(candidates)
    )


def extract_pages(data):
    """
    Aceita os formatos atuais conhecidos do Capability Scanner.
    """

    if isinstance(data, dict):

        for key in (
            "pages",
            "results",
            "capabilities",
            "entries"
        ):
            value = data.get(key)

            if isinstance(value, list):
                return value

    if isinstance(data, list):
        return data

    return []


def page_url(entry):
    if not isinstance(entry, dict):
        return None

    for key in (
        "url",
        "URL",
        "page",
        "page_url"
    ):
        value = entry.get(key)

        if value:
            return value

    return None


def normalize_entry(entry):
    """
    Preserva os dados originais, mas adiciona metadados
    úteis para o Command Engine.
    """

    url = page_url(entry)

    if not url:
        return None

    normalized = dict(entry)

    url = normalize_url(url)

    normalized["url"] = url
    normalized["is_posttest"] = is_posttest(url)

    if normalized["is_posttest"]:
        normalized["form_page"] = real_page_from_posttest(url)
    else:
        normalized["form_page"] = url

    return normalized


def merge_entries(entries):
    """
    Junta registros duplicados da mesma página.
    """

    grouped = defaultdict(list)

    for entry in entries:

        normalized = normalize_entry(entry)

        if not normalized:
            continue

        key = normalized["form_page"]

        grouped[key].append(normalized)

    pages = []

    for form_page, variants in grouped.items():

        primary = None

        for item in variants:
            if not item["is_posttest"]:
                primary = item
                break

        if primary is None:
            primary = variants[0]

        result = dict(primary)

        post_actions = []
        source_urls = []

        for item in variants:

            source_url = item.get("url")

            if source_url and source_url not in source_urls:
                source_urls.append(source_url)

            if item.get("is_posttest"):
                if source_url not in post_actions:
                    post_actions.append(source_url)

        result["source_urls"] = source_urls
        result["post_actions"] = post_actions

        result["post_action_count"] = len(post_actions)

        result["has_post"] = bool(
            post_actions
            or result.get("forms")
            or result.get("form_count")
        )

        pages.append(result)

    return pages


def count_fields(pages):
    total = 0

    for page in pages:

        fields = page.get("fields", 0)

        if isinstance(fields, int):
            total += fields

        elif isinstance(fields, list):
            total += len(fields)

    return total


def category_counter(pages):
    counter = Counter()

    for page in pages:

        categories = page.get(
            "categories",
            []
        )

        if isinstance(categories, str):
            categories = [categories]

        for category in categories:
            counter[str(category)] += 1

    return counter


def print_report(original, normalized):
    print()
    print("=" * 72)
    print("EWS CAPABILITY NORMALIZER")
    print("=" * 72)

    print()
    print(f"Registros originais : {len(original)}")
    print(f"Páginas reais       : {len(normalized)}")

    removed = len(original) - len(normalized)

    print(f"Duplicações removidas: {removed}")

    print()
    print("PÁGINAS COM POST:")

    post_pages = [
        page
        for page in normalized
        if page.get("has_post")
    ]

    for page in post_pages:

        print(
            f"  {urlparse(page['form_page']).path}"
        )

        for action in page.get(
            "post_actions",
            []
        ):
            print(
                f"      POST → {urlparse(action).path}"
            )

    print()
    print("CATEGORIAS:")

    categories = category_counter(normalized)

    for category, count in categories.most_common():
        print(
            f"  {category:<20} {count}"
        )

    print()
    print("ESTATÍSTICAS:")

    print(
        f"  Formulários : "
        f"{sum(1 for p in normalized if p.get('forms'))}"
    )

    print(
        f"  Campos      : "
        f"{count_fields(normalized)}"
    )

    print(
        f"  POST        : "
        f"{len(post_pages)}"
    )

    print()
    print("=" * 72)


def main():

    parser = argparse.ArgumentParser(
        description="Printer Assistant EWS Capability Normalizer"
    )

    parser.add_argument(
        "ip",
        help="IP da impressora"
    )

    parser.add_argument(
        "--map",
        dest="map_path",
        help="Capability Map de entrada"
    )

    parser.add_argument(
        "--output",
        help="Arquivo JSON de saída"
    )

    args = parser.parse_args()

    try:
        input_path = find_capability_map(
            args.ip,
            args.map_path
        )

    except FileNotFoundError as e:

        print(
            f"[ERRO] {e}"
        )

        return 1

    print(
        f"[OK] Capability Map encontrado:"
    )

    print(
        f"     {input_path}"
    )

    data = load_json(input_path)

    original = extract_pages(data)

    print(
        f"[OK] Registros carregados: {len(original)}"
    )

    normalized = merge_entries(
        original
    )

    output_path = args.output

    if not output_path:

        safe_ip = args.ip.replace(
            ".",
            "_"
        )

        output_path = os.path.join(
            DEFAULT_OUTPUT_DIR,
            f"normalized_{safe_ip}.json"
        )

    result = {
        "schema": "printerassistant.ews.capabilities.v1",
        "printer": {
            "ip": args.ip
        },
        "source": {
            "capability_map": os.path.abspath(
                input_path
            )
        },
        "statistics": {
            "original_records": len(original),
            "normalized_pages": len(normalized),
            "duplicates_removed": (
                len(original) - len(normalized)
            ),
            "post_pages": sum(
                1
                for page in normalized
                if page.get("has_post")
            ),
            "fields": count_fields(normalized)
        },
        "pages": normalized
    }

    save_json(
        output_path,
        result
    )

    print_report(
        original,
        normalized
    )

    print()
    print("=" * 72)
    print("CAPABILITY MAP NORMALIZADO SALVO")
    print("=" * 72)

    print()
    print("Arquivo:")
    print(
        f"  {os.path.abspath(output_path)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )