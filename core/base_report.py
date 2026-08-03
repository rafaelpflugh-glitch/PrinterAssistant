from abc import ABC, abstractmethod


class BaseReport(ABC):

    title = ""

    description = ""

    category = "Relatórios"

    @abstractmethod
    def generate(self, session):
        pass

    def print(self, session):

        return self.generate(session)