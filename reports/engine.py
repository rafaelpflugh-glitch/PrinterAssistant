"""
Motor de impressão.

Todos os relatórios serão gerados por este motor.
"""

from reports.printer import TSCPrinter


class ReportEngine:

    def __init__(self):

        self.printer = TSCPrinter()

    def imprimir(self, tspl):

        return self.printer.print(tspl)