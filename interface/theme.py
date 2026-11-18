# interface/theme.py

import tkinter as tk
from tkinter import ttk


# ============================================================
# PRINTER ASSISTANT - TEMA
# ============================================================

COR_FUNDO = "#111315"
COR_PAINEL = "#181B1F"
COR_PAINEL_2 = "#20242A"

COR_TEXTO = "#E6E9ED"
COR_TEXTO_SECUNDARIO = "#9AA3AD"

COR_BORDA = "#30363D"

COR_DESTAQUE = "#4EA1FF"
COR_SELECAO = "#263B52"

COR_ENTRADA = "#0D0F11"


# ============================================================
# APLICAÇÃO DO TEMA
# ============================================================

def aplicar_tema(root):
    """
    Aplica o tema visual global do Printer Assistant.

    O objetivo é centralizar aqui todas as definições
    visuais da interface ttk.
    """

    style = ttk.Style(root)

    # --------------------------------------------------------
    # Não usar tema nativo que possa variar entre Windows,
    # versões do Tk ou configurações do sistema.
    # --------------------------------------------------------

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass


    # ========================================================
    # FRAME
    # ========================================================

    style.configure(
        ".",
        background=COR_FUNDO,
        foreground=COR_TEXTO,
        font=(
            "Segoe UI",
            10,
        ),
    )


    style.configure(
        "TFrame",
        background=COR_FUNDO,
    )


    style.configure(
        "Panel.TFrame",
        background=COR_PAINEL,
    )


    style.configure(
        "Panel2.TFrame",
        background=COR_PAINEL_2,
    )


    # ========================================================
    # LABEL
    # ========================================================

    style.configure(
        "TLabel",
        background=COR_FUNDO,
        foreground=COR_TEXTO,
    )


    style.configure(
        "Secondary.TLabel",
        background=COR_FUNDO,
        foreground=COR_TEXTO_SECUNDARIO,
    )


    style.configure(
        "Title.TLabel",
        background=COR_FUNDO,
        foreground=COR_TEXTO,
        font=(
            "Segoe UI",
            20,
            "bold",
        ),
    )


    style.configure(
        "Heading.TLabel",
        background=COR_FUNDO,
        foreground=COR_TEXTO,
        font=(
            "Segoe UI",
            17,
            "bold",
        ),
    )


    # ========================================================
    # BUTTON
    # ========================================================

    style.configure(
        "TButton",
        background=COR_PAINEL_2,
        foreground=COR_TEXTO,
        bordercolor=COR_BORDA,
        lightcolor=COR_BORDA,
        darkcolor=COR_BORDA,
        padding=(
            12,
            7,
        ),
        font=(
            "Segoe UI",
            10,
            "bold",
        ),
    )


    style.map(
        "TButton",

        background=[
            (
                "active",
                COR_SELECAO,
            ),
            (
                "pressed",
                COR_SELECAO,
            ),
            (
                "disabled",
                COR_PAINEL,
            ),
        ],

        foreground=[
            (
                "disabled",
                COR_TEXTO_SECUNDARIO,
            ),
        ],
    )


    style.configure(
        "Accent.TButton",
        background=COR_DESTAQUE,
        foreground="#FFFFFF",
        bordercolor=COR_DESTAQUE,
        padding=(
            12,
            7,
        ),
        font=(
            "Segoe UI",
            10,
            "bold",
        ),
    )


    style.map(
        "Accent.TButton",

        background=[
            (
                "active",
                "#6AB2FF",
            ),
            (
                "pressed",
                "#3989DE",
            ),
            (
                "disabled",
                COR_PAINEL,
            ),
        ],

        foreground=[
            (
                "disabled",
                COR_TEXTO_SECUNDARIO,
            ),
        ],
    )


    # ========================================================
    # TREEVIEW
    # ========================================================

    style.configure(
        "Treeview",
        background=COR_PAINEL,
        foreground=COR_TEXTO,
        fieldbackground=COR_PAINEL,
        bordercolor=COR_BORDA,
        lightcolor=COR_BORDA,
        darkcolor=COR_BORDA,
        rowheight=30,
        font=(
            "Segoe UI",
            10,
        ),
    )


    style.configure(
        "Treeview.Heading",
        background=COR_PAINEL_2,
        foreground=COR_TEXTO,
        bordercolor=COR_BORDA,
        lightcolor=COR_BORDA,
        darkcolor=COR_BORDA,
        font=(
            "Segoe UI",
            10,
            "bold",
        ),
    )


    style.map(
        "Treeview",

        background=[
            (
                "selected",
                COR_SELECAO,
            ),
        ],

        foreground=[
            (
                "selected",
                COR_TEXTO,
            ),
        ],
    )


    style.map(
        "Treeview.Heading",

        background=[
            (
                "active",
                COR_SELECAO,
            ),
        ],
    )


    # ========================================================
    # SCROLLBAR
    # ========================================================

    style.configure(
        "Vertical.TScrollbar",
        background=COR_PAINEL_2,
        troughcolor=COR_FUNDO,
        bordercolor=COR_FUNDO,
        arrowcolor=COR_TEXTO_SECUNDARIO,
    )


    style.configure(
        "Horizontal.TScrollbar",
        background=COR_PAINEL_2,
        troughcolor=COR_FUNDO,
        bordercolor=COR_FUNDO,
        arrowcolor=COR_TEXTO_SECUNDARIO,
    )


    style.map(
        "Vertical.TScrollbar",
        background=[
            (
                "active",
                COR_SELECAO,
            ),
        ],
    )


    style.map(
        "Horizontal.TScrollbar",
        background=[
            (
                "active",
                COR_SELECAO,
            ),
        ],
    )


    # ========================================================
    # ENTRY
    # ========================================================

    style.configure(
        "TEntry",
        fieldbackground=COR_ENTRADA,
        foreground=COR_TEXTO,
        bordercolor=COR_BORDA,
        lightcolor=COR_BORDA,
        darkcolor=COR_BORDA,
        insertcolor=COR_TEXTO,
    )


    # ========================================================
    # COMBOBOX
    # ========================================================

    style.configure(
        "TCombobox",
        fieldbackground=COR_ENTRADA,
        background=COR_PAINEL,
        foreground=COR_TEXTO,
        bordercolor=COR_BORDA,
        lightcolor=COR_BORDA,
        darkcolor=COR_BORDA,
        arrowcolor=COR_TEXTO,
        insertcolor=COR_TEXTO,
    )

    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COR_ENTRADA)],
        selectbackground=[("readonly", COR_SELECAO)],
        selectforeground=[("readonly", COR_TEXTO)],
    )


    # ========================================================
    # CHECKBUTTON
    # ========================================================

    style.configure(
        "TCheckbutton",
        background=COR_FUNDO,
        foreground=COR_TEXTO,
    )


    style.map(
        "TCheckbutton",

        background=[
            (
                "active",
                COR_FUNDO,
            ),
        ],

        foreground=[
            (
                "active",
                COR_TEXTO,
            ),
        ],
    )


    # ========================================================
    # RADIOBUTTON
    # ========================================================

    style.configure(
        "TRadiobutton",
        background=COR_FUNDO,
        foreground=COR_TEXTO,
    )


    style.map(
        "TRadiobutton",

        background=[
            (
                "active",
                COR_FUNDO,
            ),
        ],

        foreground=[
            (
                "active",
                COR_TEXTO,
            ),
        ],
    )


    # ========================================================
    # SEPARADOR
    # ========================================================

    style.configure(
        "TSeparator",
        background=COR_BORDA,
    )


    # ========================================================
    # NOTEBOOK
    # ========================================================

    style.configure(
        "TNotebook",
        background=COR_FUNDO,
        bordercolor=COR_BORDA,
    )


    style.configure(
        "TNotebook.Tab",
        background=COR_PAINEL_2,
        foreground=COR_TEXTO_SECUNDARIO,
        padding=(
            12,
            7,
        ),
    )


    style.map(
        "TNotebook.Tab",

        background=[
            (
                "selected",
                COR_PAINEL,
            ),
            (
                "active",
                COR_SELECAO,
            ),
        ],

        foreground=[
            (
                "selected",
                COR_TEXTO,
            ),
        ],
    )


    # ========================================================
    # BARRA DE PROGRESSO
    # ========================================================

    style.configure(
        "TProgressbar",
        background=COR_DESTAQUE,
        troughcolor=COR_PAINEL_2,
        bordercolor=COR_BORDA,
        lightcolor=COR_DESTAQUE,
        darkcolor=COR_DESTAQUE,
    )


    # ========================================================
    # JANELA PRINCIPAL
    # ========================================================

    try:
        root.configure(
            background=COR_FUNDO
        )
    except tk.TclError:
        pass


# ============================================================
# APLICAÇÃO SIMPLES EM JANELAS Toplevel
# ============================================================

def aplicar_tema_janela(janela):
    """
    Aplica o fundo da janela a uma janela Toplevel
    ou outra janela Tkinter.
    """

    try:
        janela.configure(
            background=COR_FUNDO
        )
    except tk.TclError:
        pass