from tools.form_extractor import analisar_tudo

forms = analisar_tudo()

print("=" * 60)

print("FORMULÁRIOS ENCONTRADOS")

print("=" * 60)

print()

for form in forms:

    print("-" * 60)

    print("Arquivo :", form["arquivo"])

    print("Method  :", form["method"])

    print("Action  :", form["action"])

    print()

    print("Campos:")

    for campo in form["campos"]:

        print(
            "   ",
            campo["nome"],
            "(",
            campo["tipo"],
            ")"
        )

    print()