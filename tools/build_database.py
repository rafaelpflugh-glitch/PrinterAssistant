import os
import json
from bs4 import BeautifulSoup

PASTA = "ews_dump"

db = {
    "pages": [],
    "forms": [],
    "actions": [],
    "inputs": [],
    "selects": [],
    "links": [],
    "scripts": []
}


def add(lista, item):
    if item not in lista:
        lista.append(item)


for raiz, dirs, arquivos in os.walk(PASTA):

    for arquivo in arquivos:

        if not arquivo.endswith(".html"):
            continue

        caminho = os.path.join(raiz, arquivo)

        try:
            html = open(
                caminho,
                encoding="utf-8",
                errors="ignore"
            ).read()
        except:
            continue

        soup = BeautifulSoup(html, "html.parser")

        add(db["pages"], caminho)

        # LINKS

        for a in soup.find_all("a", href=True):

            add(
                db["links"],
                {
                    "page": caminho,
                    "text": a.get_text(strip=True),
                    "href": a["href"]
                }
            )

        # FORMS

        for form in soup.find_all("form"):

            acao = form.get("action")
            metodo = form.get("method")

            add(
                db["forms"],
                {
                    "page": caminho,
                    "action": acao,
                    "method": metodo
                }
            )

            if acao:
                add(db["actions"], acao)

            for inp in form.find_all("input"):

                add(
                    db["inputs"],
                    {
                        "page": caminho,
                        "action": acao,
                        "type": inp.get("type"),
                        "name": inp.get("name"),
                        "value": inp.get("value")
                    }
                )

            for sel in form.find_all("select"):

                opcoes = []

                for op in sel.find_all("option"):

                    opcoes.append({
                        "value": op.get("value"),
                        "text": op.get_text(strip=True)
                    })

                add(
                    db["selects"],
                    {
                        "page": caminho,
                        "action": acao,
                        "name": sel.get("name"),
                        "options": opcoes
                    }
                )

        # SCRIPTS

        for s in soup.find_all("script"):

            if s.get("src"):

                add(
                    db["scripts"],
                    {
                        "page": caminho,
                        "src": s["src"]
                    }
                )


os.makedirs("database", exist_ok=True)

with open(
    "database/mx611dhe.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        db,
        f,
        indent=4,
        ensure_ascii=False
    )

print()

print("="*60)

print("BANCO CRIADO")

print("="*60)

print("Páginas :", len(db["pages"]))
print("Forms   :", len(db["forms"]))
print("Actions :", len(db["actions"]))
print("Inputs  :", len(db["inputs"]))
print("Selects :", len(db["selects"]))
print("Links   :", len(db["links"]))
print("Scripts :", len(db["scripts"]))