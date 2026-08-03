from core.registry import Registry


# TOOLS

from tools.pjl import PJLTool
from tools.reset import ResetTool
from tools.firmware import FirmwareTool


# REPORTS

from reports.ativo import ReportAtivo


# WORKFLOWS

# futuramente:
# from workflow.reset_total import ResetTotal


def criar_registry():


    registry = Registry()


    # ======================================================
    # TOOLS
    # ======================================================

    registry.register_tool(

        PJLTool()

    )


    registry.register_tool(

        ResetTool()

    )


    registry.register_tool(

        FirmwareTool()

    )


    # ======================================================
    # REPORTS
    # ======================================================

    registry.register_report(

        ReportAtivo()

    )


    # ======================================================
    # WORKFLOWS
    # ======================================================

    # registry.register_workflow(
    #
    #     ResetTotal()
    #
    # )


    return registry