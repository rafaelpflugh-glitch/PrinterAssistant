from abc import ABC, abstractmethod


class BaseTool(ABC):


    name = ""

    description = ""

    category = ""

    icon = ""

    actions = {}



    def __init__(self):

        if not self.name:

            raise ValueError(
                "Tool precisa definir atributo 'name'"
            )



    # =====================================================
    # EXECUÇÃO
    # =====================================================

    @abstractmethod
    def execute(
        self,
        session,
        action=None,
        **kwargs
    ):

        pass



    # =====================================================
    # INFORMAÇÕES
    # =====================================================

    def info(self):

        return {

            "name": self.name,

            "description": self.description,

            "category": self.category,

            "icon": self.icon,

            "actions": self.actions

        }



    # =====================================================
    # ACTIONS
    # =====================================================

    def has_action(
        self,
        action
    ):

        return action in self.actions



    def list_actions(self):

        return list(
            self.actions.keys()
        )



    # =====================================================
    # CAPABILITIES
    # =====================================================

    def capabilities(self):

        return {

            "name": self.name,

            "category": self.category,

            "actions": self.list_actions()

        }