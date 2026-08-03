from core.validator import Validator

from core.executor import Executor


class Router:

    def __init__(self, session):

        self.validator = Validator(session)

        self.executor = Executor(session)

    def run(self, intent):

        erro = self.validator.validate()

        if erro:

            return erro

        return self.executor.execute(

            intent.tool,

            intent.action,

            **(intent.arguments or {})

        )