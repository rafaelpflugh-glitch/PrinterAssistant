"""
============================================================
PRINTER ASSISTANT
REGISTRY
============================================================

Registro central do sistema.

Responsável por armazenar:

    • Tools
    • Reports
    • Workflows

Não executa nada.
Não conhece regras de negócio.
============================================================
"""


class Registry:

    def __init__(self):

        self.tools = {}

        self.reports = {}

        self.workflows = {}

    # =====================================================
    # TOOLS
    # =====================================================

    def register(
        self,
        tool
    ):

        if not hasattr(
            tool,
            "name"
        ):

            raise ValueError(
                "Ferramenta sem atributo 'name'"
            )

        self.tools[
            tool.name
        ] = tool

    def register_tool(
        self,
        tool
    ):

        self.register(
            tool
        )

    def get(
        self,
        name
    ):

        return self.tools.get(
            name
        )

    def tool(
        self,
        name
    ):

        return self.tools[
            name
        ]

    def exists(
        self,
        name
    ):

        return name in self.tools

    def all(self):

        return list(
            self.tools.values()
        )

    def names(self):

        return list(
            self.tools.keys()
        )

    # =====================================================
    # REPORTS
    # =====================================================

    def register_report(
        self,
        report
    ):

        if not hasattr(
            report,
            "title"
        ):

            raise ValueError(
                "Report sem atributo 'title'"
            )

        self.reports[
            report.title
        ] = report

    def get_report(
        self,
        title
    ):

        return self.reports.get(
            title
        )

    def report(
        self,
        title
    ):

        return self.reports[
            title
        ]

    def reports_all(self):

        return list(
            self.reports.values()
        )

    def report_titles(self):

        return list(
            self.reports.keys()
        )

    # =====================================================
    # WORKFLOWS
    # =====================================================

    def register_workflow(
        self,
        workflow
    ):

        if not hasattr(
            workflow,
            "name"
        ):

            raise ValueError(
                "Workflow sem atributo 'name'"
            )

        self.workflows[
            workflow.name
        ] = workflow

    def get_workflow(
        self,
        name
    ):

        return self.workflows.get(
            name
        )

    def workflow(
        self,
        name
    ):

        return self.workflows[
            name
        ]

    def workflows_all(self):

        return list(
            self.workflows.values()
        )

    def workflow_names(self):

        return list(
            self.workflows.keys()
        )

    # =====================================================
    # LIMPEZA
    # =====================================================

    def clear(self):

        self.tools.clear()

        self.reports.clear()

        self.workflows.clear()

    # =====================================================
    # DEBUG
    # =====================================================

    def summary(self):

        return {

            "tools":
                self.names(),

            "reports":
                self.report_titles(),

            "workflows":
                self.workflow_names()

        }

    def list_everything(self):

        print()

        print(
            "=" * 60
        )

        print(
            "TOOLS"
        )

        print(
            "=" * 60
        )

        for tool in self.tools.values():

            print(

                getattr(
                    tool,
                    "icon",
                    "🔧"
                ),

                tool.name

            )

        print()

        print(
            "=" * 60
        )

        print(
            "REPORTS"
        )

        print(
            "=" * 60
        )

        for report in self.reports.values():

            print(
                report.title
            )

        print()

        print(
            "=" * 60
        )

        print(
            "WORKFLOWS"
        )

        print(
            "=" * 60
        )

        for workflow in self.workflows.values():

            print(
                workflow.name
            )