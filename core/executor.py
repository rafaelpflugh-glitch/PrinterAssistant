"""
============================================================
PRINTER ASSISTANT
EXECUTOR
============================================================

Camada de execução de comandos.

Responsável por encaminhar comandos para o ToolManager.

O Executor não conhece a lógica interna das ferramentas.
============================================================
"""

from core.tool_manager import ToolManager


class Executor:

    def __init__(
        self,
        session
    ):

        self.session = session

        self.manager = ToolManager(
            session
        )

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(
        self,
        tool,
        action=None,
        **kwargs
    ):

        return self.manager.execute(
            tool,
            action,
            **kwargs
        )

    # ========================================================
    # HTTP GET
    # ========================================================

    def get(
        self,
        endpoint,
        **kwargs
    ):

        return self.execute(

            "http",

            "get",

            endpoint=endpoint,

            **kwargs

        )

    # ========================================================
    # HTTP POST
    # ========================================================

    def post(
        self,
        endpoint,
        **kwargs
    ):

        return self.execute(

            "http",

            "post",

            endpoint=endpoint,

            **kwargs

        )

    # ========================================================
    # COMPATIBILIDADE
    # ========================================================

    def executar(
        self,
        tool,
        action=None,
        **kwargs
    ):

        return self.execute(
            tool,
            action,
            **kwargs
        )