from core.registry import Registry

from tools.pjl_tool import PJLTool

from tools.reset import ResetTool

from tools.firmware import FirmwareTool

class ToolManager:

    """
    Gerencia todas as ferramentas do Printer Assistant.

    O Dispatcher conversa apenas com o ToolManager.

    O ToolManager conversa apenas com as ferramentas.

    Nenhum outro módulo deve instanciar ferramentas diretamente.
    """

    def __init__(self, session):

        self.session = session

        self.registry = Registry()

        self._register_builtin_tools()

    # ==========================================================
    # REGISTRO
    # ==========================================================

    def register(self, tool):

        self.registry.register(tool)

    def _register_builtin_tools(self):

        self.register(PJLTool())

        self.register(ResetTool())

        self.register(FirmwareTool())

    # ==========================================================
    # EXECUÇÃO
    # ==========================================================

    def execute(

        self,

        tool,

        action=None,

        **kwargs

    ):

        ferramenta = self.registry.get(tool)

        if ferramenta is None:

            return {

                "sucesso": False,

                "tool": tool,

                "action": action,

                "mensagem": f"Ferramenta '{tool}' não encontrada.",

                "resultado": None

            }

        try:

            return ferramenta.execute(

                self.session,

                action=action,

                **kwargs

            )

        except Exception as erro:

            return {

                "sucesso": False,

                "tool": tool,

                "action": action,

                "mensagem": str(erro),

                "resultado": None

            }

    # ==========================================================
    # COMPATIBILIDADE
    # ==========================================================

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

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def exists(self, tool):

        return self.registry.get(tool) is not None

    def tools(self):

        return [

            ferramenta.info()

            for ferramenta in self.registry.all()

        ]

    def names(self):

        return [

            ferramenta.name

            for ferramenta in self.registry.all()

        ]

    def categories(self):

        categorias = {}

        for ferramenta in self.registry.all():

            categoria = ferramenta.category or "Geral"

            categorias.setdefault(

                categoria,

                []

            ).append(

                ferramenta.name

            )

        return categorias

    def capabilities(self):

        dados = {}

        for ferramenta in self.registry.all():

            if hasattr(

                ferramenta,

                "capabilities"

            ):

                dados[ferramenta.name] = ferramenta.capabilities()

            else:

                dados[ferramenta.name] = []

        return dados