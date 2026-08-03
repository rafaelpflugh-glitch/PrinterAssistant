from core.registry import ToolRegistry

from tools.report_ativo import ReportAtivoTool
from tools.firmware import FirmwareTool
from tools.reset import ResetTool
from tools.pjl import PJLTool


def build_registry():

    registry = ToolRegistry()

    registry.register(

        ReportAtivoTool()

    )

    registry.register(

        FirmwareTool()

    )

    registry.register(

        ResetTool()

    )

    registry.register(

        PJLTool()

    )

    return registry