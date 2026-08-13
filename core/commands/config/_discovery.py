"""
Printer Assistant - PJL Configuration Discovery

Descobre as variáveis PJL anunciadas pela impressora.

IMPORTANTE:
- não altera configurações;
- não executa SET;
- não executa DEFAULT;
- usa o IP somente como endereço de conexão;
- a capacidade real de escrita será testada posteriormente.
"""

from collections import defaultdict


class PJLConfigDiscovery:
    def __init__(self, writer, parser):
        self.writer = writer
        self.parser = parser

    def discover(self):
        """
        Executa INFO VARIABLES e transforma a resposta
        em uma estrutura organizada.
        """

        resposta = self.writer.enviar(
            "@PJL INFO VARIABLES"
        )

        variaveis = self.parser.parse_info_variables(
            resposta
        )

        return variaveis

    @staticmethod
    def agrupar_por_categoria(variaveis):
        """
        Agrupa variáveis pela categoria fornecida pelo parser.
        """

        grupos = defaultdict(list)

        for variavel in variaveis:
            categoria = variavel.get(
                "categoria",
                "GERAL",
            )

            grupos[categoria].append(
                variavel
            )

        return dict(grupos)

    @staticmethod
    def somente_gravaveis(variaveis):
        """
        Retorna variáveis que não estão marcadas como READONLY.

        Isso NÃO significa que DEFAULT seja permitido.
        É apenas uma primeira filtragem.
        """

        return [
            variavel
            for variavel in variaveis
            if not variavel.get(
                "readonly",
                False,
            )
        ]

    @staticmethod
    def somente_readonly(variaveis):
        return [
            variavel
            for variavel in variaveis
            if variavel.get(
                "readonly",
                False,
            )
        ]