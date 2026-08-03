from core.registry import Registry
from tools.pjl_tool import PJLTool
from tools.reset import ResetTool
from tools.firmware import FirmwareTool


registry = Registry()


registry.register(PJLTool())
registry.register(ResetTool())
registry.register(FirmwareTool())


print(
    registry.summary()
)


registry.list_everything()