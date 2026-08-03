import importlib


class WorkflowEngine:

    def __init__(self, dispatcher, session):

        self.dispatcher = dispatcher
        self.session = session

    # -----------------------------------------

    def executar(self, workflow_name):

        modulo = importlib.import_module(
            f"workflows.{workflow_name}"
        )

        workflow = modulo.WORKFLOW

        print()

        print("=" * 60)
        print(workflow["name"])
        print("=" * 60)

        for passo in workflow["steps"]:

            print()

            print("[EXECUTANDO]", passo)

            self.dispatcher.execute(

                passo,

                self.session

            )

        print()

        print("=" * 60)
        print("Workflow concluído.")
        print("=" * 60)