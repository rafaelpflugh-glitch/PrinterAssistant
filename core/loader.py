import importlib
import pkgutil

import tools

from core.registry import Registry


def carregar_ferramentas():

    registry = Registry()

    for module in pkgutil.iter_modules(

        tools.__path__

    ):

        m = importlib.import_module(

            f"tools.{module.name}"

        )

        if hasattr(

            m,

            "tool"

        ):

            registry.register(

                m.tool

            )

    return registry