from core.session import Session
from core.tool_manager import ToolManager


session = Session()

manager = ToolManager(session)


print()

print("=" * 60)
print("TOOL MANAGER")
print("=" * 60)

print()

print("TOOLS")

for nome in manager.names():

    print(" -", nome)

print()

print("REPORTS")

for relatorio in manager.reports():

    print(" -", relatorio)

print()

print("CATEGORIES")

for categoria, ferramentas in manager.categories().items():

    print(categoria, "->", ferramentas)

print()

print("CAPABILITIES")

for nome, capacidades in manager.capabilities().items():

    print()

    print(nome)

    print(capacidades)