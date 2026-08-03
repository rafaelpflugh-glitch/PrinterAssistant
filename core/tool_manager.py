from core.registry import Registry
from core.result import ToolResult


from tools.pjl_tool import PJLTool
from tools.reset import ResetTool
from tools.firmware import FirmwareTool



class ToolManager:


    """
    Camada central de gerenciamento das ferramentas.

    Responsabilidades:

    - registrar tools
    - localizar tools
    - executar tools
    - expor capacidades

    Não conhece lógica interna das ferramentas.

    """



    def __init__(
        self,
        session
    ):

        self.session = session

        self.registry = Registry()

        self.load_builtin_tools()



    # =====================================================
    # LOAD
    # =====================================================


    def load_builtin_tools(self):


        tools = [

            PJLTool(),

            ResetTool(),

            FirmwareTool()

        ]


        for tool in tools:

            self.register(tool)



    # =====================================================
    # REGISTRO
    # =====================================================


    def register(
        self,
        tool
    ):


        self.registry.register(
            tool
        )



    # =====================================================
    # EXECUÇÃO
    # =====================================================


    def execute(
        self,
        tool,
        action=None,
        **kwargs
    ):


        ferramenta = self.registry.get(
            tool
        )


        if ferramenta is None:


            return ToolResult.erro(

                tool,

                action,

                f"Ferramenta '{tool}' não encontrada"

            ).to_dict()



        if action and not ferramenta.has_action(action):


            return ToolResult.erro(

                tool,

                action,

                "Ação não suportada"

            ).to_dict()



        try:


            return ferramenta.execute(

                self.session,

                action,

                **kwargs

            )


        except Exception as erro:


            return ToolResult.erro(

                tool,

                action,

                str(erro)

            ).to_dict()



    # =====================================================
    # COMPATIBILIDADE
    # =====================================================


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



    # =====================================================
    # CONSULTAS
    # =====================================================


    def exists(
        self,
        tool
    ):

        return self.registry.exists(
            tool
        )



    def tools(self):

        return [

            tool.info()

            for tool in self.registry.all()

        ]



    def names(self):

        return self.registry.names()



    def categories(self):


        resultado = {}


        for tool in self.registry.all():


            categoria = (

                tool.category

                or

                "Geral"

            )


            resultado.setdefault(

                categoria,

                []

            ).append(

                tool.name

            )


        return resultado



    def capabilities(self):


        return {


            tool.name:

            tool.capabilities()

            for tool

            in self.registry.all()


        }