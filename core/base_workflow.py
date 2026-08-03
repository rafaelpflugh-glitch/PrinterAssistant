from abc import ABC, abstractmethod


class BaseWorkflow(ABC):

    name = ""

    description = ""

    @abstractmethod
    def execute(self, session):
        pass