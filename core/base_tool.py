"""
Printer Assistant
BaseTool

Classe base para todas as ferramentas.
"""

from abc import ABC, abstractmethod

from core.action import Action


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

        # Cada instância possui seu próprio registro
        self.actions = {}

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
    # REGISTRO DE ACTIONS
    # =====================================================

    def register_action(self, action: Action):

        self.actions[action.name] = action

    def get_action(self, name):

        return self.actions.get(name)

    def has_action(self, action):

        return action in self.actions

    def list_actions(self):

        return list(self.actions.keys())

    # =====================================================
    # INFO
    # =====================================================

    def info(self):

        return {

            "name": self.name,

            "description": self.description,

            "category": self.category,

            "icon": self.icon,

            "actions": {

                nome: {

                    "description": acao.description

                }

                for nome, acao in self.actions.items()

            }

        }

    # =====================================================
    # CAPABILITIES
    # =====================================================

    def capabilities(self):

        return {

            "name": self.name,

            "category": self.category,

            "actions": self.list_actions()

        }