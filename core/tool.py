from abc import ABC, abstractmethod


class Tool(ABC):

    name = "tool"

    description = ""

    category = "general"

    @abstractmethod
    def run(self, **kwargs):
        pass

    def info(self):

        return {

            "name": self.name,

            "description": self.description,

            "category": self.category

        }