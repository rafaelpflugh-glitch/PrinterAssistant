class Registry:

    def __init__(self):

        self.tools = {}

        self.reports = {}

        self.workflows = {}

    # ----------------------------

    def register_tool(self, tool):

        self.tools[tool.name] = tool

    # ----------------------------

    def register_report(self, report):

        self.reports[report.title] = report

    # ----------------------------

    def register_workflow(self, workflow):

        self.workflows[workflow.name] = workflow

    # ----------------------------

    def tool(self, name):

        return self.tools[name]

    # ----------------------------

    def report(self, title):

        return self.reports[title]

    # ----------------------------

    def workflow(self, name):

        return self.workflows[name]

    # ----------------------------

    def list_everything(self):

        print()

        print("="*60)

        print("TOOLS")

        print("="*60)

        for t in self.tools.values():

            print(

                t.icon,

                t.name

            )

        print()

        print("="*60)

        print("REPORTS")

        print("="*60)

        for r in self.reports.values():

            print(

                r.title

            )

        print()

        print("="*60)

        print("WORKFLOWS")

        print("="*60)

        for w in self.workflows.values():

            print(

                w.name

            )