from abc import ABC, abstractmethod


class BaseTool(ABC):

    name = ""

    description = ""

    category = ""

    icon = ""

    actions = {}


    @abstractmethod
    def execute(self, session, action=None, **kwargs):
        pass


    def info(self):

        return {

            "name": self.name,

            "description": self.description,

            "category": self.category,

            "icon": self.icon,

            "actions": self.actions

        }


    def has_action(self, action):

        return action in self.actions


    def list_actions(self):

        return list(self.actions.keys())