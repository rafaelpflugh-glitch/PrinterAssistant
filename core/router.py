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
from core.validator import Validator
from core.executor import Executor


class Router:

    """
    Controla o fluxo principal.

    Intent
        ↓
    Validator
        ↓
    Executor
    """

    def __init__(self, session):

        self.session = session

        self.validator = Validator(session)

        self.executor = Executor(session)

    # ======================================================

    def run(self, intent):

        erro = self.validator.validate(intent)

        if erro:

            return erro

        return self.executor.execute(

            intent.tool,

            intent.action,

            **intent.arguments

        )
            intent.tool,

            intent.action,

            **(intent.arguments or {})

        )