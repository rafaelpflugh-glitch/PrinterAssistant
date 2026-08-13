"""
Printer Assistant - PJL Capabilities

Modelo de dados para representar aquilo que a impressora
declara aceitar via PJL.

Não executa alterações na impressora.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PJLVariable:
    nome: str

    valor: Optional[str] = None

    tipo: Optional[str] = None

    valores: List[str] = field(default_factory=list)

    minimo: Optional[str] = None
    maximo: Optional[str] = None

    readonly: bool = False

    familia: str = "GERAL"

    origem: str = "INFO VARIABLES"

    def aceita_valor(self, valor: str) -> bool:
        """
        Verifica se um valor está dentro do que a impressora
        declarou aceitar.

        Não significa que a variável seja gravável.
        """

        valor = str(valor).strip().upper()

        if self.valores:
            return valor in {
                str(v).strip().upper()
                for v in self.valores
            }

        return True

    @property
    def gravavel_candidata(self) -> bool:
        """
        Indica se a variável parece ser candidata a escrita.

        Isto é apenas uma classificação inicial.
        A confirmação real será feita posteriormente por probe.
        """

        return not self.readonly


@dataclass
class PJLCapabilities:
    """
    Conjunto completo de capacidades descobertas.
    """

    modelo: Optional[str] = None
    serial: Optional[str] = None
    firmware: Optional[str] = None

    variaveis: List[PJLVariable] = field(default_factory=list)

    def adicionar(self, variavel: PJLVariable):
        """
        Adiciona ou substitui uma variável.
        """

        nome = variavel.nome.upper()

        for indice, existente in enumerate(self.variaveis):
            if existente.nome.upper() == nome:
                self.variaveis[indice] = variavel
                return

        self.variaveis.append(variavel)

    def obter(self, nome: str) -> Optional[PJLVariable]:
        nome = nome.strip().upper()

        for variavel in self.variaveis:
            if variavel.nome.upper() == nome:
                return variavel

        return None

    def todas(self):
        return sorted(
            self.variaveis,
            key=lambda item: item.nome.upper(),
        )

    def gravaveis_candidatas(self):
        return [
            variavel
            for variavel in self.todas()
            if variavel.gravavel_candidata
        ]

    def readonly(self):
        return [
            variavel
            for variavel in self.todas()
            if variavel.readonly
        ]

    def por_familia(self, familia: str):
        familia = familia.upper()

        return [
            variavel
            for variavel in self.todas()
            if variavel.familia.upper() == familia
        ]
