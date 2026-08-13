"""
Printer Assistant - PJL Configuration Parser

Parser genérico para blocos retornados por:

@PJL INFO VARIABLES
@PJL INFO CONFIG
@PJL INFO USTATUS

O parser não assume uma lista fixa de variáveis.
"""

import re


class PJLConfigParser:

    # ==========================================================
    # INFO VARIABLES
    # ==========================================================

    @staticmethod
    def parse_variables(texto):
        """
        Converte INFO VARIABLES em um dicionário.

        Exemplo:

            DENSITY=3 [2 RANGE]
                    1
                    5

        vira:

            {
                "DENSITY": {
                    "valor": "3",
                    "tipo": "RANGE",
                    "opcoes": ["1", "5"],
                }
            }
        """

        resultado = {}

        linhas = texto.splitlines()

        atual = None

        for linha in linhas:

            linha = linha.rstrip()

            if not linha.strip():
                continue

            # Ignora cabeçalho PJL
            if linha.strip().upper().startswith("@PJL"):
                continue

            # --------------------------------------------------
            # Variável principal
            # --------------------------------------------------

            match = re.match(
                r"^([A-Za-z0-9_:\\]+)=(.*?)\s+\[(.*?)\]$",
                linha.strip(),
            )

            if match:

                nome = match.group(1).strip()

                valor = match.group(2).strip()

                descricao = match.group(3).strip()

                partes = descricao.split()

                quantidade = None
                tipo = None

                if partes:
                    try:
                        quantidade = int(partes[0])
                    except ValueError:
                        pass

                if len(partes) >= 2:
                    tipo = partes[1]

                atual = {
                    "valor": valor,
                    "tipo": tipo,
                    "quantidade": quantidade,
                    "opcoes": [],
                }

                resultado[nome] = atual

                continue

            # --------------------------------------------------
            # Opções da variável anterior
            # --------------------------------------------------

            if atual is not None:

                valor = linha.strip()

                if valor:
                    atual["opcoes"].append(
                        valor
                    )

        return resultado

    # ==========================================================
    # BUSCA DE VARIÁVEL
    # ==========================================================

    @staticmethod
    def get_variable(
        variables,
        nome,
    ):
        """
        Busca uma variável ignorando maiúsculas/minúsculas.
        """

        alvo = nome.strip().upper()

        for chave, valor in variables.items():

            if chave.upper() == alvo:
                return valor

        return None

    # ==========================================================
    # VALOR
    # ==========================================================

    @staticmethod
    def get_value(
        variables,
        nome,
    ):
        variavel = PJLConfigParser.get_variable(
            variables,
            nome,
        )

        if variavel is None:
            return None

        return variavel.get(
            "valor"
        )

    # ==========================================================
    # OPÇÕES
    # ==========================================================

    @staticmethod
    def get_options(
        variables,
        nome,
    ):
        variavel = PJLConfigParser.get_variable(
            variables,
            nome,
        )

        if variavel is None:
            return []

        return variavel.get(
            "opcoes",
            [],
        )