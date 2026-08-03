from abc import ABC, abstractmethod


class BaseTool(ABC):

    name = ""

    description = ""

    category = ""

    icon = ""

    @abstractmethod
    def execute(self, session, **kwargs):
        pass

    def info(self):

        return {

            "name": self.name,

            "description": self.description,

            "category": self.category,

            "icon": self.icon

        }