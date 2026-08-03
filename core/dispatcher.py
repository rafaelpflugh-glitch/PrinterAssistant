from core.router import Router


class Dispatcher:

    def __init__(self, session):

        self.router = Router(session)

    def dispatch(self, intent):

        return self.router.run(intent)