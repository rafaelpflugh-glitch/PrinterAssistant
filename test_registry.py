from core.build_registry import build_registry

registry = build_registry()

print()

print("TOOLS INSTALADAS")

print("----------------")

for categoria, lista in registry.categories().items():

    print()

    print(categoria)

    for tool in lista:

        print("  •", tool.name)