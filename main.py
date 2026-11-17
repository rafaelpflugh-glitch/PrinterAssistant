"""
============================================================
PRINTER ASSISTANT
MAIN
============================================================

Ponto de entrada da aplicação gráfica.

A interface principal é responsável por:

    - descobrir impressoras;
    - identificar equipamentos;
    - realizar a coleta completa;
    - exibir a PrinterView;
    - iniciar as ferramentas da interface.

O código antigo de diagnóstico/CLI não é iniciado aqui.

============================================================
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import tkinter as tk

from interface.main_window import MainWindow


# ============================================================
# INICIAR APLICAÇÃO
# ============================================================

def iniciar():
    """
    Cria e inicia a janela principal do Printer Assistant.
    """

    app = MainWindow()

    app.mainloop()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        iniciar()

    except KeyboardInterrupt:

        print()
        print("Printer Assistant encerrado.")