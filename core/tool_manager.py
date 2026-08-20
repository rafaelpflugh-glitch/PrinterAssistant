"""
============================================================
Printer Assistant
Tool Manager
============================================================

Camada central responsável por registrar e executar
todas as ferramentas do sistema.
============================================================
"""

from core.registry import Registry
from core.result import ToolResult


# ============================================================
# TOOLS
# ============================================================

from tools.scanner_tool import ScannerTool
from tools.pjl_tool import PJLTool
from tools.reset import ResetTool
from tools.firmware import FirmwareTool
from tools.http_tool import HTTPTool


# ============================================================
# REPORTS
# ============================================================

from reports.config_report import ConfigReport


class ToolManager:

    """
    Camada central de gerenciamento.

    Responsabilidades:

        • Registrar ferramentas
        • Registrar relatórios
        • Localizar ferramentas
        • Executar ferramentas
        • Expor capacidades

    Não conhece lógica interna das ferramentas.
    """

    # =====================================================
    # CONSTRUTOR
    # =====================================================

    def __init__(
        self,
        session
    ):

        self.session = session

        self.registry = Registry()

        self.load_builtin_tools()

        self.load_builtin_reports()

    # =====================================================
    # LOAD TOOLS
    # =====================================================

    def load_builtin_tools(self):

        ferramentas = [

            ScannerTool(),

            PJLTool(),

            ResetTool(),

            FirmwareTool(),

            HTTPTool()

        ]

        for ferramenta in ferramentas:

            self.register(
                ferramenta
            )

    # =====================================================
    # LOAD REPORTS
    # =====================================================

    def load_builtin_reports(self):

        relatorios = [

            ConfigReport()

        ]

        for relatorio in relatorios:

            self.registry.register_report(
                relatorio
            )

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

                f"Ferramenta '{tool}' "
                "não encontrada."

            ).to_dict()

        if (
            action
            and
            not ferramenta.has_action(
                action
            )
        ):

            return ToolResult.erro(

                tool,

                action,

                f"A ferramenta '{tool}' "
                f"não suporta a ação '{action}'."

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

    def get(
        self,
        tool
    ):

        return self.registry.get(
            tool
        )

    def tools(self):

        return [

            ferramenta.info()

            for ferramenta

            in self.registry.all()

        ]

    def names(self):

        return self.registry.names()

    def categories(self):

        categorias = {}

        for ferramenta in self.registry.all():

            categoria = (

                getattr(
                    ferramenta,
                    "category",
                    None
                )

                or

                "Geral"

            )

            categorias.setdefault(

                categoria,

                []

            ).append(

                ferramenta.name

            )

        return categorias

    def capabilities(self):

        return {

            ferramenta.name:

            ferramenta.capabilities()

            for ferramenta

            in self.registry.all()

        }

    # =====================================================
    # RELATÓRIOS
    # =====================================================

    def report(
        self,
        title
    ):

        return self.registry.report(
            title
        )

    def reports(self):

        return self.registry.reports_all()

    # =====================================================
    # DEBUG
    # =====================================================

    def info(self):

        return {

            "tools":

                self.registry.names(),

            "reports":

                [

                    r.title

                    for r

                    in self.registry.reports_all()

                ],

            "workflows":

                list(
                    self.registry.workflows.keys()
                )

        }