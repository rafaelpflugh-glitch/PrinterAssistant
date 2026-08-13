from core.session import Session
from core.tool_manager import ToolManager

session = Session()

manager = ToolManager(session)

resultado = manager.execute(

    "scanner"

)

print()

print(resultado)

print()

print(session.info())