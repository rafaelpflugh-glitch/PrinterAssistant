from core.session import PrinterSession

from core.tool_manager import ToolManager


sessao = PrinterSession()

manager = ToolManager(sessao)

print()

print("="*60)

print("TOOLS")

print("="*60)

print()

for nome, tool in manager.tools.items():

    print(tool.name)

    print()

    for action in tool.list_actions():

        print("   ", action)

    print()