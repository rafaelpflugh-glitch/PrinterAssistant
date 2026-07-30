import json
import sys

BANCO = "database/mx611dhe.json"


with open(BANCO, encoding="utf-8") as f:
    db = json.load(f)


if len(sys.argv) < 2:
    print("Uso:")
    print("python explorer.py palavra")
    exit()


busca = " ".join(sys.argv[1:]).lower()

print("=" * 70)
print("PESQUISA:", busca)
print("=" * 70)

encontrou = False


def procurar(lista, titulo):

    global encontrou

    resultados = []

    for item in lista:

        texto = json.dumps(item, ensure_ascii=False).lower()

        if busca in texto:
            resultados.append(item)

    if resultados:

        encontrou = True

        print()
        print("-" * 70)
        print(titulo)
        print("-" * 70)

        for r in resultados:

            print(json.dumps(
                r,
                indent=4,
                ensure_ascii=False
            ))


procurar(db["pages"], "PÁGINAS")
procurar(db["forms"], "FORMS")
procurar(db["actions"], "ACTIONS")
procurar(db["inputs"], "INPUTS")
procurar(db["selects"], "SELECTS")
procurar(db["links"], "LINKS")
procurar(db["scripts"], "SCRIPTS")

if not encontrou:

    print()
    print("Nada encontrado.")