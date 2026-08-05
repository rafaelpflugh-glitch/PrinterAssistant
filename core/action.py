"""
Printer Assistant
Action

Representa uma ação executável pertencente a uma ferramenta.

Uma Action conhece:

- nome
- descrição
- executor
- parser

Fluxo:

executor() -> resposta bruta

parser() -> resultado estruturado
"""

from typing import Callable, Any


class Action:

    def __init__(
        self,
        name: str,
        description: str,
        executor: Callable,
        parser: Callable | None = None
    ):

        self.name = name

        self.description = description

        self.executor = executor

        self.parser = parser

    # =====================================================
    # EXECUÇÃO
    # =====================================================

    def run(
        self,
        context=None,
        **kwargs
    ):

        """
        Executa a Action.

        context:
            normalmente será uma instância de PJL,
            Firmware,
            Reset,
            etc.

        kwargs:
            parâmetros extras para futuras Actions.
        """

        if context is None:

            resultado = self.executor(**kwargs)

        else:

            resultado = self.executor(
                context,
                **kwargs
            )

        if self.parser is not None:

            return self.parser(resultado)

        return resultado

    # =====================================================
    # METADADOS
    # =====================================================

    def info(self):

        return {

            "name": self.name,

            "description": self.description,

            "has_parser": self.parser is not None

        }

    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"Action("
            f"name='{self.name}', "
            f"description='{self.description}'"
            f")"

        )