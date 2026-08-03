from dataclasses import dataclass


@dataclass
class Tool:

    id: str

    nome: str

    categoria: str

    descricao: str

    callback: callable


class ToolRegistry:

    def __init__(self):

        self._tools = {}

    # ---------------------------------------

    def registrar(self, tool: Tool):

        self._tools[tool.id] = tool

    # ---------------------------------------

    def obter(self, tool_id):

        return self._tools.get(tool_id)

    # ---------------------------------------

    def listar(self):

        return list(self._tools.values())

    # ---------------------------------------

    def categorias(self):

        resultado = {}

        for tool in self._tools.values():

            resultado.setdefault(
                tool.categoria,
                []
            ).append(tool)

        return resultado


registry = ToolRegistry()