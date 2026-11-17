import tkinter as tk
from tkinter import ttk, messagebox
import time
import inspect
import threading
from datetime import datetime
import re
import os

from services.report_service import (
    ReportError,
    ReportService,
)
from core.version import __version__


# ============================================================
# CLASSE
# ============================================================

class PrinterView(ttk.Frame):
    """
    Ficha visual de uma impressora.

    Recebe um PrinterDevice e apresenta os dados retornados
    por device.to_dict().

    Regras desta interface:

        - Tema escuro.
        - Não exibir Part Number.
        - Não processar Part Number.
        - Exibir serial da impressora.
        - Exibir serial do toner quando disponível.
        - Exibir serial da unidade de imagem quando disponível.
        - Fusor não possui campo de serial.
        - Garantia para unidade de imagem exige idade de até 2 anos E nível acima de 50%.
        - Origem do contador não é exibida.
        - Informações textuais são selecionáveis.
        - Relatórios são acionados pelo ReportService.
        - RMA é acionado pelo módulo reports.rma.
        - RMA utiliza os dados já coletados do PrinterDevice.
        - RMA imprime exclusivamente na TSC configurada.
    """

    # ========================================================
    # CORES
    # ========================================================

    COR_FUNDO = "#111315"
    COR_PAINEL = "#181b1f"
    COR_PAINEL_2 = "#1d2125"
    COR_BORDA = "#30353a"

    COR_TEXTO = "#e6e6e6"
    COR_TEXTO_SECUNDARIO = "#9aa0a6"
    COR_TEXTO_FRACO = "#70777e"

    COR_DESTAQUE = "#4fc3f7"
    COR_ONLINE = "#55d66b"
    COR_OFFLINE = "#e05252"
    COR_ATENCAO = "#e7b84b"

    COR_SELECAO = "#315b73"

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def __init__(
        self,
        master,
        device=None,
        on_refresh=None,
        on_back=None,
    ):
        super().__init__(
            master,
            padding=0,
            style="PrinterView.TFrame",
        )

        self.device = device
        self.on_refresh = on_refresh
        self.on_back = on_back

        self._criar_estilos()
        self._criar_interface()

        if device:
            self.atualizar(device)

    # ========================================================
    # ESTILOS
    # ========================================================

    def _criar_estilos(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "PrinterView.TFrame",
            background=self.COR_FUNDO,
        )

        style.configure(
            "PrinterView.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 10),
        )

        style.configure(
            "PrinterView.Secondary.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
        )

        style.configure(
            "PrinterView.Title.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 18, "bold"),
        )

        style.configure(
            "PrinterView.Model.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 12, "bold"),
        )

        style.configure(
            "PrinterView.Section.TLabel",
            background=self.COR_PAINEL,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 11, "bold"),
        )

        style.configure(
            "PrinterView.FieldTitle.TLabel",
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
        )

        style.configure(
            "PrinterView.FieldValue.TLabel",
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "PrinterView.Serial.TLabel",
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 11, "bold"),
        )

        style.configure(
            "PrinterView.TLabelframe",
            background=self.COR_PAINEL,
            foreground=self.COR_TEXTO,
            bordercolor=self.COR_BORDA,
            relief="solid",
            borderwidth=1,
        )

        style.configure(
            "PrinterView.TLabelframe.Label",
            background=self.COR_PAINEL,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "PrinterView.TButton",
            background="#252a2f",
            foreground=self.COR_TEXTO,
            bordercolor=self.COR_BORDA,
            lightcolor="#252a2f",
            darkcolor="#252a2f",
            padding=8,
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "PrinterView.TButton",
            background=[
                ("active", "#30373d"),
                ("pressed", "#20252a"),
                ("disabled", "#191c1f"),
            ],
            foreground=[
                ("disabled", "#5f666d"),
            ],
        )

        style.configure(
            "PrinterView.Report.TButton",
            background="#20262b",
            foreground=self.COR_TEXTO,
            bordercolor="#3a434a",
            lightcolor="#20262b",
            darkcolor="#20262b",
            padding=7,
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "PrinterView.Report.TButton",
            background=[
                ("active", "#2b3942"),
                ("pressed", "#1b2227"),
                ("disabled", "#191c1f"),
            ],
        )

        style.configure(
            "PrinterView.RMA.TButton",
            background="#26333a",
            foreground=self.COR_TEXTO,
            bordercolor="#4a6875",
            lightcolor="#26333a",
            darkcolor="#26333a",
            padding=7,
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "PrinterView.RMA.TButton",
            background=[
                ("active", "#31505d"),
                ("pressed", "#1d292f"),
                ("disabled", "#191c1f"),
            ],
            foreground=[
                ("disabled", "#5f666d"),
            ],
        )

        style.configure(
            "PrinterView.Producao.TButton",
            background="#315b73",
            foreground="#ffffff",
            bordercolor="#4fc3f7",
            lightcolor="#315b73",
            darkcolor="#315b73",
            padding=7,
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "PrinterView.Producao.TButton",
            background=[
                ("active", "#4fc3f7"),
                ("pressed", "#244356"),
                ("disabled", "#191c1f"),
            ],
            foreground=[
                ("disabled", "#5f666d"),
            ],
        )

        style.configure(
            "PrinterView.RMA.TCombobox",
            fieldbackground=self.COR_PAINEL_2,
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            arrowcolor=self.COR_TEXTO_SECUNDARIO,
            bordercolor=self.COR_BORDA,
            lightcolor=self.COR_PAINEL_2,
            darkcolor=self.COR_PAINEL_2,
            selectbackground=self.COR_SELECAO,
            selectforeground="#ffffff",
        )

        style.map(
            "PrinterView.RMA.TCombobox",
            fieldbackground=[
                ("readonly", self.COR_PAINEL_2),
                ("focus", self.COR_PAINEL_2),
                ("active", self.COR_PAINEL_2),
            ],
            foreground=[
                ("readonly", self.COR_TEXTO),
                ("focus", self.COR_TEXTO),
                ("active", self.COR_TEXTO),
            ],
            selectbackground=[
                ("readonly", self.COR_SELECAO),
                ("focus", self.COR_SELECAO),
            ],
            selectforeground=[
                ("readonly", "#ffffff"),
                ("focus", "#ffffff"),
            ],
        )

        style.configure(
            "PrinterView.Supply.TEntry",
            fieldbackground=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            insertcolor=self.COR_TEXTO,
            bordercolor=self.COR_BORDA,
            lightcolor=self.COR_PAINEL_2,
            darkcolor=self.COR_PAINEL_2,
            padding=7,
            font=("Segoe UI", 10),
        )

        style.map(
            "PrinterView.Supply.TEntry",
            fieldbackground=[
                ("focus", self.COR_PAINEL_2),
                ("active", self.COR_PAINEL_2),
            ],
            bordercolor=[
                ("focus", self.COR_DESTAQUE),
            ],
        )

        style.configure(
            "PrinterView.Supply.TButton",
            background="#26333a",
            foreground=self.COR_TEXTO,
            bordercolor="#4a6875",
            lightcolor="#26333a",
            darkcolor="#26333a",
            padding=8,
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "PrinterView.Supply.TButton",
            background=[
                ("active", "#31505d"),
                ("pressed", "#1d292f"),
                ("disabled", "#191c1f"),
            ],
        )

        style.configure(
            "PrinterView.Horizontal.TProgressbar",
            troughcolor="#292e33",
            background=self.COR_DESTAQUE,
            bordercolor="#292e33",
            lightcolor=self.COR_DESTAQUE,
            darkcolor=self.COR_DESTAQUE,
            thickness=10,
        )

        style.configure(
            "PrinterView.Vertical.TScrollbar",
            background="#252a2f",
            troughcolor=self.COR_FUNDO,
            bordercolor=self.COR_FUNDO,
            arrowcolor="#8b9299",
        )

    # ========================================================
    # TEXTO SELECIONÁVEL
    # ========================================================

    def _texto_selecionavel(
        self,
        parent,
        texto="—",
        font=None,
        altura=1,
        largura=None,
        background=None,
        foreground=None,
    ):

        if font is None:
            font = ("Segoe UI", 10)

        if background is None:
            background = self.COR_PAINEL_2

        if foreground is None:
            foreground = self.COR_TEXTO

        widget = tk.Text(
            parent,
            height=altura,
            width=largura if largura else 1,
            font=font,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            background=background,
            foreground=foreground,
            insertbackground=foreground,
            selectbackground=self.COR_SELECAO,
            selectforeground="#ffffff",
            wrap="none",
            padx=0,
            pady=0,
            exportselection=False,
        )

        widget.insert(
            "1.0",
            str(texto),
        )

        widget.configure(
            state="disabled"
        )

        return widget

    # ========================================================
    # DEFINIR TEXTO
    # ========================================================

    def _definir_texto(
        self,
        widget,
        texto,
    ):

        widget.configure(
            state="normal"
        )

        widget.delete(
            "1.0",
            "end",
        )

        widget.insert(
            "1.0",
            str(texto),
        )

        widget.configure(
            state="disabled"
        )

    # ========================================================
    # INTERFACE
    # ========================================================

    def _criar_interface(self):

        self.columnconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            2,
            weight=1,
        )

        # ----------------------------------------------------
        # CABEÇALHO
        # ----------------------------------------------------

        header = tk.Frame(
            self,
            background=self.COR_FUNDO,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(14, 10),
        )

        header.columnconfigure(
            0,
            weight=1,
        )

        self.lbl_titulo = ttk.Label(
            header,
            text=f"PRINTER ASSISTANT  {__version__}",
            style="PrinterView.Title.TLabel",
        )

        self.lbl_titulo.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.lbl_estado = tk.Label(
            header,
            text="●  OFFLINE",
            background=self.COR_FUNDO,
            foreground=self.COR_OFFLINE,
            font=("Segoe UI", 10, "bold"),
        )

        self.lbl_estado.grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.lbl_modelo = ttk.Label(
            header,
            text="Impressora",
            style="PrinterView.Model.TLabel",
        )

        self.lbl_modelo.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(3, 0),
        )

        self.lbl_ip = ttk.Label(
            header,
            text="",
            style="PrinterView.Secondary.TLabel",
        )

        self.lbl_ip.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(1, 0),
        )

        # ----------------------------------------------------
        # IDENTIFICAÇÃO
        # ----------------------------------------------------

        identificacao = ttk.LabelFrame(
            self,
            text=" IDENTIFICAÇÃO ",
            padding=10,
            style="PrinterView.TLabelframe",
        )

        identificacao.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 10),
        )

        for coluna in range(4):

            identificacao.columnconfigure(
                coluna,
                weight=1,
            )

        self._campo(
            identificacao,
            "Fabricante",
            0,
            0,
        )

        self._campo(
            identificacao,
            "Modelo",
            0,
            1,
        )

        self._campo(
            identificacao,
            "Família",
            0,
            2,
        )

        self._campo(
            identificacao,
            "Tipo",
            0,
            3,
        )

        self._campo(
            identificacao,
            "Serial",
            1,
            0,
            serial=True,
        )

        self._campo(
            identificacao,
            "Firmware",
            1,
            1,
        )

        self._campo(
            identificacao,
            "Contador",
            1,
            2,
        )

        # ----------------------------------------------------
        # ÁREA PRINCIPAL
        # ----------------------------------------------------

        principal = tk.Frame(
            self,
            background=self.COR_FUNDO,
        )

        principal.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=18,
        )

        principal.columnconfigure(
            0,
            weight=4,
        )

        principal.columnconfigure(
            1,
            weight=1,
        )

        principal.rowconfigure(
            0,
            weight=1,
        )

        # ----------------------------------------------------
        # CONSUMÍVEIS
        # ----------------------------------------------------

        supplies_frame = ttk.LabelFrame(
            principal,
            text=" CONSUMÍVEIS ",
            padding=10,
            style="PrinterView.TLabelframe",
        )

        supplies_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6),
        )

        supplies_frame.columnconfigure(
            0,
            weight=1,
        )

        supplies_frame.rowconfigure(
            0,
            weight=1,
        )

        canvas = tk.Canvas(
            supplies_frame,
            highlightthickness=0,
            borderwidth=0,
            background=self.COR_PAINEL,
        )

        scrollbar = ttk.Scrollbar(
            supplies_frame,
            orient="vertical",
            command=canvas.yview,
            style="PrinterView.Vertical.TScrollbar",
        )

        canvas.configure(
            yscrollcommand=scrollbar.set,
        )

        canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.supplies_container = tk.Frame(
            canvas,
            background=self.COR_PAINEL,
        )

        self.supplies_window = canvas.create_window(
            (0, 0),
            window=self.supplies_container,
            anchor="nw",
        )

        def atualizar_scroll(event=None):

            canvas.configure(
                scrollregion=canvas.bbox("all")
            )

        def ajustar_largura(event):

            canvas.itemconfigure(
                self.supplies_window,
                width=event.width,
            )

        self.supplies_container.bind(
            "<Configure>",
            atualizar_scroll,
        )

        canvas.bind(
            "<Configure>",
            ajustar_largura,
        )

        def mousewheel(event):

            canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units",
            )

        def mousewheel_linux_up(event):

            canvas.yview_scroll(
                -1,
                "units",
            )

        def mousewheel_linux_down(event):

            canvas.yview_scroll(
                1,
                "units",
            )

        def ativar_mousewheel(event):

            canvas.bind_all(
                "<MouseWheel>",
                mousewheel,
            )

            canvas.bind_all(
                "<Button-4>",
                mousewheel_linux_up,
            )

            canvas.bind_all(
                "<Button-5>",
                mousewheel_linux_down,
            )

        def desativar_mousewheel(event):

            canvas.unbind_all(
                "<MouseWheel>"
            )

            canvas.unbind_all(
                "<Button-4>"
            )

            canvas.unbind_all(
                "<Button-5>"
            )

        canvas.bind(
            "<Enter>",
            ativar_mousewheel,
        )

        canvas.bind(
            "<Leave>",
            desativar_mousewheel,
        )

        self.supplies_canvas = canvas

        # ====================================================
        # RELATÓRIOS E AÇÕES
        # ====================================================

        self.reports_frame = ttk.LabelFrame(
            principal,
            text=" RELATÓRIOS E AÇÕES ",
            padding=8,
            style="PrinterView.TLabelframe",
        )

        self.reports_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0),
        )

        self.reports_frame.columnconfigure(
            0,
            weight=1,
        )

        # ----------------------------------------------------
        # RELATÓRIO DE ATIVO
        # ----------------------------------------------------

        self.btn_relatorio_ativo = ttk.Button(
            self.reports_frame,
            text="RELATÓRIO DE ATIVO",
            command=self._clicar_relatorio_ativo,
            style="PrinterView.Report.TButton",
        )

        self.btn_relatorio_ativo.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=3,
        )

        # ----------------------------------------------------
        # CONFIGURAÇÃO E SUPRIMENTOS
        # ----------------------------------------------------

        self.btn_config_suprimentos = ttk.Button(
            self.reports_frame,
            text="CONFIG. E SUPRIMENTOS",
            command=self._clicar_configuracao_suprimentos,
            style="PrinterView.Report.TButton",
        )

        self.btn_config_suprimentos.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=3,
        )

        # ----------------------------------------------------
        # ANÁLISE DE UNIDADE DE IMAGEM
        # ----------------------------------------------------

        self.btn_analise_imagem = ttk.Button(
            self.reports_frame,
            text="ANÁLISE UNIDADE IMAGEM",
            command=self._clicar_analise_unidade_imagem,
            style="PrinterView.Report.TButton",
        )

        self.btn_analise_imagem.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=3,
        )

        # ----------------------------------------------------
        # DEMONSTRAÇÃO
        # ----------------------------------------------------

        self.btn_demonstracao = ttk.Button(
            self.reports_frame,
            text="DEMONSTRAÇÃO",
            command=self._clicar_demonstracao,
            style="PrinterView.Report.TButton",
        )

        self.btn_demonstracao.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=3,
        )

        # ====================================================
        # RELATÓRIO RMA
        # ====================================================

        self.btn_relatorio_rma = ttk.Button(
            self.reports_frame,
            text="RELATÓRIO RMA",
            command=self._clicar_relatorio_rma,
            style="PrinterView.RMA.TButton",
        )

        self.btn_relatorio_rma.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=3,
        )

        # ====================================================
        # PRODUÇÃO DE ETIQUETAS
        # ====================================================

        self.btn_producao_etiqueta = ttk.Button(
            self.reports_frame,
            text="PRODUÇÃO ETIQUETAS",
            command=self._abrir_producao_etiqueta,
            style="PrinterView.Producao.TButton",
        )

        self.btn_producao_etiqueta.grid(
            row=5,
            column=0,
            sticky="ew",
            pady=3,
        )

        # ----------------------------------------------------
        # SEPARADOR VISUAL
        # ----------------------------------------------------

        ttk.Separator(
            self.reports_frame,
            orient="horizontal",
        ).grid(
            row=6,
            column=0,
            sticky="ew",
            pady=6,
        )

        ttk.Label(
            self.reports_frame,
            text="Preview disponível antes de imprimir.",
            style="PrinterView.Secondary.TLabel",
            justify="left",
            wraplength=170,
        ).grid(
            row=7,
            column=0,
            sticky="nw",
            pady=(0, 2),
        )

        # ----------------------------------------------------
        # RODAPÉ
        # ----------------------------------------------------

        footer = tk.Frame(
            self,
            background=self.COR_FUNDO,
        )

        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=18,
            pady=(10, 14),
        )

        footer.columnconfigure(
            0,
            weight=1,
        )

        self.lbl_fontes = tk.Label(
            footer,
            text="",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            anchor="w",
        )

        self.lbl_fontes.grid(
            row=0,
            column=0,
            sticky="w",
        )

        botoes = tk.Frame(
            footer,
            background=self.COR_FUNDO,
        )

        botoes.grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.btn_voltar = ttk.Button(
            botoes,
            text="Voltar",
            command=self._clicar_voltar,
            style="PrinterView.TButton",
        )

        self.btn_voltar.pack(
            side="left",
            padx=(0, 8),
        )

        self.btn_atualizar = ttk.Button(
            botoes,
            text="Atualizar",
            command=self._clicar_atualizar,
            style="PrinterView.TButton",
        )

        self.btn_atualizar.pack(
            side="left",
        )

    # ========================================================
    # CAMPO DE IDENTIFICAÇÃO
    # ========================================================

    def _campo(
        self,
        parent,
        titulo,
        row,
        column,
        serial=False,
    ):

        frame = tk.Frame(
            parent,
            background=self.COR_PAINEL_2,
        )

        frame.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=4,
            pady=3,
        )

        frame.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            frame,
            text=titulo,
            style="PrinterView.FieldTitle.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        label = self._texto_selecionavel(
            frame,
            "—",
            font=(
                "Segoe UI",
                12 if serial else 11,
                "bold",
            ),
            background=self.COR_PAINEL_2,
        )

        label.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        nomes_atributos = {
            "Fabricante": "fabricante",
            "Modelo": "modelo",
            "Família": "familia",
            "Tipo": "tipo",
            "Serial": "serial",
            "Firmware": "firmware",
            "Contador": "contador",
        }

        atributo = nomes_atributos.get(
            titulo,
            titulo.lower().replace(
                " ",
                "_",
            ),
        )

        setattr(
            self,
            f"campo_{atributo}",
            label,
        )

    # ========================================================
    # NORMALIZAR TIPO DE CONSUMÍVEL
    # ========================================================

    @staticmethod
    def _tipo_consumivel(
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):
            return ""

        tipo = supply.get("tipo")

        if tipo:

            texto = str(
                tipo
            ).strip().lower()

            if texto in (
                "toner",
                "cartucho",
                "cartridge",
            ):
                return "toner"

            if texto in (
                "unidade_imagem",
                "unidade imagem",
                "imaging",
                "imaging unit",
                "photoconductor",
                "fotocondutor",
                "drum",
            ):
                return "unidade_imagem"

            if texto in (
                "fusor",
                "fuser",
                "maintenance",
                "maintenance kit",
                "kit manutencao",
                "kit manutenção",
            ):
                return "fusor"

        nome = (
            supply.get("nome")
            or supply.get("name")
            or supply.get("descricao")
            or supply.get("description")
            or ""
        )

        texto = str(
            nome
        ).strip().lower()

        if "maintenance kit" in texto:
            return "fusor"

        if (
            "fusor" in texto
            or "fuser" in texto
        ):
            return "fusor"

        if (
            "toner" in texto
            or "cartucho" in texto
            or "cartridge" in texto
        ):
            return "toner"

        if (
            "unidade de imagem" in texto
            or "imaging unit" in texto
            or "imaging" in texto
            or "photoconductor" in texto
            or "drum" in texto
            or "fotocondutor" in texto
        ):
            return "unidade_imagem"

        return ""

    # ========================================================
    # VALIDAÇÃO DE GARANTIA (NÍVEL > 50% E IDADE MÁXIMA DE 2 ANOS)
    # ========================================================

    @staticmethod
    def _verificar_garantia(serial, nivel):
        """
        Valida a garantia da unidade de imagem com base em duas regras:
        1. O nível deve estar estritamente acima de 50%.
        2. A idade baseada no ano de fabricação extraído do serial deve ser de no máximo 2 anos.
        """
        if nivel is not None:
            try:
                if float(nivel) <= 50:
                    return False
            except (ValueError, TypeError):
                pass

        if not serial:
            return None

        serial_limpo = str(serial).strip().upper()
        if len(serial_limpo) < 5:
            return None

        match = re.search(r'[A-Z]{3}(\d{2})', serial_limpo)
        if not match:
            match = re.search(r'^[A-Z]*(\d{2})', serial_limpo)

        if match:
            try:
                digitos_ano = match.group(1)
                ano_fab = 2000 + int(digitos_ano)
                ano_atual = datetime.now().year
                idade = ano_atual - ano_fab

                if 0 <= idade <= 2:
                    return True
                else:
                    return False
            except (ValueError, TypeError):
                pass

        return None

    # ========================================================
    # ATUALIZAÇÃO DA TELA
    # ========================================================

    def atualizar(
        self,
        device=None,
    ):

        if device is not None:
            self.device = device

        if self.device is None:
            return

        try:

            dados = self.device.to_dict()

        except Exception as erro:

            messagebox.showerror(
                "Printer Assistant",
                (
                    "Não foi possível atualizar "
                    "a ficha da impressora.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

            return

        if not isinstance(
            dados,
            dict,
        ):
            return

        identificacao = dados.get(
            "identificacao",
            {},
        )

        if not isinstance(
            identificacao,
            dict,
        ):
            identificacao = {}

        conectividade = dados.get(
            "conectividade",
            {},
        )

        if not isinstance(
            conectividade,
            dict,
        ):
            conectividade = {}

        modelo = identificacao.get(
            "modelo",
            "Impressora",
        )

        self.lbl_modelo.config(
            text=str(modelo)
        )

        ip = dados.get(
            "ip",
            "",
        )

        if not ip:

            ip = getattr(
                self.device,
                "ip",
                "",
            )

        self.lbl_ip.config(
            text=str(ip)
        )

        estado = str(
            dados.get(
                "estado",
                "OFFLINE",
            )
        ).upper()

        if estado in (
            "ONLINE",
            "EXCELENTE",
            "OK",
            "READY",
        ):

            self.lbl_estado.config(
                text="●  ONLINE",
                foreground=self.COR_ONLINE,
            )

        elif estado in (
            "ATENÇÃO",
            "ATENCAO",
            "WARNING",
        ):

            self.lbl_estado.config(
                text="●  ATENÇÃO",
                foreground=self.COR_ATENCAO,
            )

        else:

            self.lbl_estado.config(
                text=f"●  {estado}",
                foreground=self.COR_OFFLINE,
            )

        self._definir_texto(
            self.campo_fabricante,
            identificacao.get(
                "fabricante",
                "Desconhecido",
            ),
        )

        self._definir_texto(
            self.campo_modelo,
            identificacao.get(
                "modelo",
                "Desconhecido",
            ),
        )

        self._definir_texto(
            self.campo_familia,
            identificacao.get(
                "familia",
                "",
            ),
        )

        self._definir_texto(
            self.campo_tipo,
            identificacao.get(
                "tipo",
                "",
            ),
        )

        self._definir_texto(
            self.campo_serial,
            identificacao.get(
                "serial",
                "Desconhecido",
            ),
        )

        firmware = identificacao.get(
            "firmware",
            dados.get(
                "firmware",
                "Desconhecido",
            ),
        )

        self._definir_texto(
            self.campo_firmware,
            firmware,
        )

        contador = identificacao.get(
            "contador"
        )

        if contador is None:

            contador_texto = "Desconhecido"

        else:

            try:

                contador_texto = (
                    f"{int(contador):,}"
                    .replace(",", ".")
                )

            except (
                TypeError,
                ValueError,
            ):

                contador_texto = str(
                    contador
                )

        self._definir_texto(
            self.campo_contador,
            contador_texto,
        )

        self._atualizar_supplies(
            dados.get(
                "supplies",
                [],
            )
        )

        fontes = []

        nomes = (
            "pjl",
            "sysdebug",
            "snmp",
            "web",
            "ipp",
        )

        for nome in nomes:

            ativo = conectividade.get(
                nome,
                False,
            )

            simbolo = (
                "●"
                if ativo
                else "○"
            )

            fontes.append(
                f"{nome.upper()} {simbolo}"
            )

        self.lbl_fontes.config(
            text="    ".join(fontes)
        )

    # ========================================================
    # CONSUMÍVEIS
    # ========================================================

    def _atualizar_supplies(
        self,
        supplies,
    ):

        for widget in (
            self.supplies_container.winfo_children()
        ):
            widget.destroy()

        if not supplies:

            tk.Label(
                self.supplies_container,
                text="Nenhum consumível encontrado.",
                background=self.COR_PAINEL,
                foreground=self.COR_TEXTO_SECUNDARIO,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(
                anchor="w",
                pady=10,
            )

            return

        for numero, supply in enumerate(
            supplies,
            start=1,
        ):

            self._criar_supply_card(
                numero,
                supply,
            )

        self.supplies_container.update_idletasks()

        self.supplies_canvas.configure(
            scrollregion=self.supplies_canvas.bbox(
                "all"
            )
        )

    # ========================================================
    # CARD DE CONSUMÍVEL
    # ========================================================

    def _criar_supply_card(
        self,
        numero,
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):
            return

        card = tk.Frame(
            self.supplies_container,
            background=self.COR_PAINEL_2,
            highlightbackground=self.COR_BORDA,
            highlightcolor=self.COR_BORDA,
            highlightthickness=1,
            bd=0,
        )

        card.pack(
            fill="x",
            pady=4,
        )

        card.columnconfigure(
            0,
            weight=1,
        )

        nome = (
            supply.get("nome")
            or supply.get("name")
            or f"Consumível {numero}"
        )

        tipo = self._tipo_consumivel(
            supply
        )

        tipo_texto = self._texto_tipo(
            tipo
        )

        nivel = supply.get(
            "nivel"
        )

        if nivel is None:

            nivel = supply.get(
                "percentual"
            )

        if nivel is None:

            nivel = 0

        try:

            nivel = float(
                nivel
            )

        except (
            TypeError,
            ValueError,
        ):

            nivel = 0

        nivel = max(
            0,
            min(
                100,
                nivel,
            ),
        )

        titulo = str(
            nome
        )

        if (
            tipo_texto
            and tipo_texto.lower()
            not in titulo.lower()
        ):

            titulo = (
                f"{titulo} — {tipo_texto}"
            )

        titulo_widget = (
            self._texto_selecionavel(
                card,
                titulo,
                font=(
                    "Segoe UI",
                    11,
                    "bold",
                ),
                background=self.COR_PAINEL_2,
            )
        )

        titulo_widget.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=(8, 0),
        )

        percentual = (
            self._texto_selecionavel(
                card,
                f"{nivel:.0f} %",
                font=(
                    "Segoe UI",
                    14,
                    "bold",
                ),
                largura=7,
                background=self.COR_PAINEL_2,
            )
        )

        percentual.grid(
            row=0,
            column=1,
            sticky="e",
            padx=10,
            pady=(8, 0),
        )

        barra = ttk.Progressbar(
            card,
            maximum=100,
            value=nivel,
            style=(
                "PrinterView."
                "Horizontal.TProgressbar"
            ),
        )

        barra.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=10,
            pady=(5, 7),
        )

        capacidade = supply.get(
            "capacidade"
        )

        restante = supply.get(
            "restante"
        )

        consumido = supply.get(
            "consumido"
        )

        detalhes = []

        if capacidade is not None:

            detalhes.append(
                "Capacidade: "
                + self._numero(
                    capacidade
                )
            )

        if restante is not None:

            detalhes.append(
                "Restante: "
                + self._numero(
                    restante
                )
            )

        if consumido is not None:

            detalhes.append(
                "Consumido: "
                + self._numero(
                    consumido
                )
            )

        condicao = supply.get(
            "condicao"
        )

        if condicao:

            detalhes.append(
                f"Condição: {condicao}"
            )

        if detalhes:

            detalhes_widget = (
                self._texto_selecionavel(
                    card,
                    "    •    ".join(
                        detalhes
                    ),
                    font=(
                        "Segoe UI",
                        9,
                    ),
                    background=(
                        self.COR_PAINEL_2
                    ),
                    foreground=(
                        self.COR_TEXTO_SECUNDARIO
                    ),
                )
            )

            detalhes_widget.grid(
                row=2,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=10,
                pady=(0, 3),
            )

        # ----------------------------------------------------
        # SERIAL
        # ----------------------------------------------------

        if tipo != "fusor":

            serial = (
                supply.get(
                    "numero_serie"
                )
                or supply.get(
                    "serial"
                )
            )

            if serial:

                serial_widget = (
                    self._texto_selecionavel(
                        card,
                        f"Nº série: {serial}",
                        font=(
                            "Segoe UI",
                            9,
                            "bold",
                        ),
                        background=(
                            self.COR_PAINEL_2
                        ),
                    )
                )

                serial_widget.grid(
                    row=3,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    padx=10,
                    pady=(2, 0),
                )

        # ----------------------------------------------------
        # GARANTIA
        # ----------------------------------------------------

        if tipo == "unidade_imagem":

            serial_unidade = (
                supply.get("numero_serie")
                or supply.get("serial")
                or ""
            )

            garantia = supply.get(
                "garantia"
            )

            res_garantia = self._verificar_garantia(
                serial_unidade, nivel
            )

            if res_garantia is not None:
                garantia = res_garantia

            if garantia is True:

                texto = (
                    "Garantia: POSSÍVEL"
                )

                foreground = (
                    self.COR_ONLINE
                )

            elif garantia is False:

                texto = (
                    "Garantia: NÃO ELEGÍVEL"
                )

                foreground = (
                    self.COR_OFFLINE
                )

            else:

                texto = (
                    "Garantia: N/D"
                )

                foreground = (
                    self.COR_TEXTO_SECUNDARIO
                )

            garantia_widget = (
                self._texto_selecionavel(
                    card,
                    texto,
                    font=(
                        "Segoe UI",
                        9,
                        "bold",
                    ),
                    background=(
                        self.COR_PAINEL_2
                    ),
                    foreground=foreground,
                )
            )

            garantia_widget.grid(
                row=4,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=10,
                pady=(2, 8),
            )

        else:

            spacer = tk.Frame(
                card,
                height=7,
                background=self.COR_PAINEL_2,
            )

            spacer.grid(
                row=4,
                column=0,
                columnspan=2,
                sticky="ew",
            )

    # ========================================================
    # FORMATAÇÃO NUMÉRICA
    # ========================================================

    @staticmethod
    def _numero(
        valor,
    ):

        try:

            return (
                f"{int(valor):,}"
                .replace(",", ".")
            )

        except (
            TypeError,
            ValueError,
        ):

            return str(
                valor
            )

    # ========================================================
    # TEXTO DO TIPO
    # ========================================================

    @staticmethod
    def _texto_tipo(
        tipo,
    ):

        textos = {
            "toner": "Toner",
            "unidade_imagem": (
                "Unidade de imagem"
            ),
            "fusor": "Fusor",
        }

        return textos.get(
            tipo,
            str(tipo),
        )

    # ========================================================
    # REPORT SERVICE
    # ========================================================

    def _criar_report_service(
        self,
    ):

        if self.device is None:

            raise ReportError(
                "Nenhuma impressora está selecionada."
            )

        return ReportService(
            self.device
        )

    # ========================================================
    # CONFIGURAÇÃO E SUPRIMENTOS (DIRETO VIA reports.configuracao_suprimentos)
    # ========================================================

    def _clicar_configuracao_suprimentos(self):
        if self.device is None:
            messagebox.showerror(
                "Configuração e Suprimentos",
                "Nenhuma impressora está selecionada.",
                parent=self,
            )
            return

        try:
            from reports.configuracao_suprimentos import (
                preparar_relatorio_configuracao,
                imprimir_relatorio_configuracao,
                digitalizar_relatorio_configuracao,
            )
        except ImportError as erro:
            messagebox.showerror(
                "Configuração e Suprimentos",
                f"Módulo reports.configuracao_suprimentos não encontrado:\n{erro}",
                parent=self,
            )
            return

        marcas_selecionadas = {"cartucho": "GLOBAL", "unidade_imagem": "LEXMARK"}

        class _MarcasReceiver:
            def definir_marcas_suprimentos(self, m_cart, m_unid):
                marcas_selecionadas["cartucho"] = m_cart
                marcas_selecionadas["unidade_imagem"] = m_unid

        def continuar_geracao():
            try:
                m_cart = marcas_selecionadas["cartucho"]
                m_unid = marcas_selecionadas["unidade_imagem"]

                resultado = preparar_relatorio_configuracao(
                    self.device,
                    marca_cartucho=m_cart,
                    marca_unidade_imagem=m_unid,
                )
                texto = resultado.get("texto", "") if isinstance(resultado, dict) else str(resultado)

                def imprimir():
                    imprimir_relatorio_configuracao(
                        self.device,
                        marca_cartucho=m_cart,
                        marca_unidade_imagem=m_unid,
                    )

                def digitalizar():
                    retorno = digitalizar_relatorio_configuracao(
                        self.device,
                        marca_cartucho=m_cart,
                        marca_unidade_imagem=m_unid,
                    )
                    caminho = retorno.get("arquivo") if isinstance(retorno, dict) else str(retorno)
                    if caminho:
                        messagebox.showinfo(
                            "Configuração e Suprimentos",
                            f"Relatório digital gerado com sucesso.\n\nArquivo:\n{caminho}",
                            parent=self,
                        )

                self._escolher_acao_relatorio(
                    "CONFIGURAÇÃO E SUPRIMENTOS",
                    texto=texto,
                    imprimir_callback=imprimir,
                    digitalizar_callback=digitalizar,
                )
            except Exception as erro:
                messagebox.showerror("Configuração e Suprimentos", f"Erro ao gerar:\n{erro}", parent=self)

        self._solicitar_marcas_suprimentos(_MarcasReceiver(), continuar_geracao)

    _clicar_relatorio_configuracao = _clicar_configuracao_suprimentos

    def _solicitar_marcas_suprimentos(
        self,
        service,
        continuar_callback,
    ):
        """
        Solicita os fabricantes utilizados no relatório
        de Configuração e Suprimentos.
        """

        dialogo = tk.Toplevel(
            self.winfo_toplevel()
        )

        dialogo.title(
            "CONFIGURAÇÃO E SUPRIMENTOS"
        )

        dialogo.geometry(
            "560x330"
        )

        dialogo.minsize(
            520,
            300,
        )

        dialogo.resizable(
            False,
            False,
        )

        dialogo.transient(
            self.winfo_toplevel()
        )

        dialogo.grab_set()

        dialogo.configure(
            background=self.COR_FUNDO
        )

        dialogo.columnconfigure(
            0,
            weight=1,
        )

        frame = tk.Frame(
            dialogo,
            background=self.COR_FUNDO,
            padx=28,
            pady=24,
        )

        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        frame.columnconfigure(
            0,
            weight=1,
        )

        tk.Label(
            frame,
            text="CONFIGURAÇÃO E SUPRIMENTOS",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5),
        )

        tk.Label(
            frame,
            text=(
                "Selecione o fabricante dos consumíveis "
                "que constará no relatório."
            ),
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            justify="left",
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 20),
        )

        tk.Label(
            frame,
            text="FABRICANTE DO CARTUCHO DE TONER",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 5),
        )

        marca_cartucho_var = tk.StringVar(
            value="GLOBAL"
        )

        fabricante_cartucho_combo = ttk.Combobox(
            frame,
            textvariable=marca_cartucho_var,
            values=(
                "LEXMARK",
                "3I",
                "VRI",
                "GLOBAL",
            ),
            state="readonly",
            font=("Segoe UI", 10),
            style="PrinterView.RMA.TCombobox",
        )

        fabricante_cartucho_combo.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(0, 15),
        )

        tk.Label(
            frame,
            text="FABRICANTE DA UNIDADE DE IMAGEM",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(0, 5),
        )

        marca_unidade_var = tk.StringVar(
            value="LEXMARK"
        )

        fabricante_unidade_combo = ttk.Combobox(
            frame,
            textvariable=marca_unidade_var,
            values=(
                "LEXMARK",
                "3I",
                "VRI",
                "GLOBAL",
                "REM",
            ),
            state="readonly",
            font=("Segoe UI", 10),
            style="PrinterView.RMA.TCombobox",
        )

        fabricante_unidade_combo.grid(
            row=5,
            column=0,
            sticky="ew",
            pady=(0, 20),
        )

        tk.Label(
            frame,
            text=(
                "Essas informações serão utilizadas "
                "em Visualizar, Digitalizar e Imprimir."
            ),
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 8),
            justify="left",
            anchor="w",
        ).grid(
            row=6,
            column=0,
            sticky="w",
            pady=(0, 18),
        )

        botoes = tk.Frame(
            frame,
            background=self.COR_FUNDO,
        )

        botoes.grid(
            row=7,
            column=0,
            sticky="ew",
        )

        botoes.columnconfigure(
            0,
            weight=1,
        )

        resultado = {
            "confirmado": False,
        }

        def cancelar():

            resultado["confirmado"] = False

            dialogo.destroy()

        def continuar():

            marca_cartucho = (
                marca_cartucho_var.get().strip()
            )

            marca_unidade_imagem = (
                marca_unidade_var.get().strip()
            )

            if not marca_cartucho:

                messagebox.showwarning(
                    "Configuração e Suprimentos",
                    (
                        "Selecione o fabricante "
                        "do cartucho de toner."
                    ),
                    parent=dialogo,
                )

                fabricante_cartucho_combo.focus_set()

                return

            if not marca_unidade_imagem:

                messagebox.showwarning(
                    "Configuração e Suprimentos",
                    (
                        "Selecione o fabricante "
                        "da unidade de imagem."
                    ),
                    parent=dialogo,
                )

                fabricante_unidade_combo.focus_set()

                return

            try:

                service.definir_marcas_suprimentos(
                    marca_cartucho,
                    marca_unidade_imagem,
                )

            except ReportError as erro:

                messagebox.showerror(
                    "Configuração e Suprimentos",
                    str(erro),
                    parent=dialogo,
                )

                return

            except Exception as erro:

                messagebox.showerror(
                    "Configuração e Suprimentos",
                    (
                        "Não foi possível definir "
                        "os fabricantes.\n\n"
                        f"{erro}"
                    ),
                    parent=dialogo,
                )

                return

            resultado["confirmado"] = True

            dialogo.destroy()

        ttk.Button(
            botoes,
            text="CANCELAR",
            command=cancelar,
            style="PrinterView.TButton",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            botoes,
            text="CONTINUAR",
            command=continuar,
            style="PrinterView.Supply.TButton",
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

        dialogo.bind(
            "<Escape>",
            lambda event: cancelar(),
        )

        dialogo.bind(
            "<Return>",
            lambda event: continuar(),
        )

        fabricante_cartucho_combo.focus_set()

        self.wait_window(
            dialogo
        )

        if resultado["confirmado"]:

            continuar_callback()

    # ========================================================
    # ANÁLISE DE UNIDADE DE IMAGEM (DIRETO VIA reports.analise_unidade_imagem)
    # ========================================================

    def _clicar_analise_unidade_imagem(self):
        if self.device is None:
            messagebox.showerror(
                "Análise de Unidade de Imagem",
                "Nenhuma impressora está selecionada.",
                parent=self,
            )
            return

        try:
            from reports.analise_unidade_imagem import (
                preparar_analise_unidade,
                imprimir_analise_unidade,
                digitalizar_analise_unidade,
            )

            resultado = preparar_analise_unidade(self.device)
            texto = resultado.get("texto", "") if isinstance(resultado, dict) else str(resultado)

            def imprimir():
                imprimir_analise_unidade(self.device)

            def digitalizar():
                retorno = digitalizar_analise_unidade(self.device)
                caminho = retorno.get("arquivo") if isinstance(retorno, dict) else str(retorno)
                if caminho:
                    messagebox.showinfo(
                        "Análise de Unidade de Imagem",
                        f"Relatório digital gerado com sucesso.\n\nArquivo:\n{caminho}",
                        parent=self,
                    )

            self._escolher_acao_relatorio(
                "ANÁLISE DE UNIDADE DE IMAGEM",
                texto=texto,
                imprimir_callback=imprimir,
                digitalizar_callback=digitalizar,
            )
        except Exception as erro:
            messagebox.showerror("Análise de Unidade de Imagem", f"Erro ao processar:\n{erro}", parent=self)

    _clicar_analise_unidade = _clicar_analise_unidade_imagem

    # ========================================================
    # ESCOLHA DA AÇÃO DO RELATÓRIO
    # ========================================================

    def _escolher_acao_relatorio(
        self,
        titulo,
        texto=None,
        imprimir_callback=None,
        digitalizar_callback=None,
    ):
        """
        Abre a janela de ações do relatório.

        A opção DIGITALIZAR é opcional.

        Quando fornecida, ela NÃO faz nova coleta.
        O callback recebido é responsável por gerar o
        documento digital a partir dos dados já preparados.
        """

        dialogo = tk.Toplevel(
            self.winfo_toplevel()
        )

        dialogo.title(
            titulo
        )

        if digitalizar_callback:

            dialogo.geometry(
                "520x210"
            )

            dialogo.minsize(
                480,
                190,
            )

        else:

            dialogo.geometry(
                "420x210"
            )

            dialogo.minsize(
                380,
                190,
            )

        dialogo.resizable(
            False,
            False,
        )

        dialogo.transient(
            self.winfo_toplevel()
        )

        dialogo.grab_set()

        dialogo.configure(
            background=self.COR_FUNDO
        )

        frame = tk.Frame(
            dialogo,
            background=self.COR_FUNDO,
            padx=25,
            pady=22,
        )

        frame.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            frame,
            text=titulo,
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        ).pack(
            anchor="w",
            pady=(0, 10),
        )

        tk.Label(
            frame,
            text=(
                "O que deseja fazer com este relatório?"
            ),
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(
            anchor="w",
            pady=(0, 20),
        )

        resultado = {
            "acao": None,
        }

        botoes = tk.Frame(
            frame,
            background=self.COR_FUNDO,
        )

        botoes.pack(
            fill="x",
            side="bottom",
        )

        def escolher(
            acao
        ):

            resultado["acao"] = acao

            dialogo.destroy()

        ttk.Button(
            botoes,
            text="CANCELAR",
            command=lambda: escolher(
                None
            ),
            style="PrinterView.TButton",
        ).pack(
            side="left",
        )

        if imprimir_callback:

            ttk.Button(
                botoes,
                text="IMPRIMIR",
                command=lambda: escolher(
                    "imprimir"
                ),
                style="PrinterView.Report.TButton",
            ).pack(
                side="right",
            )

        if digitalizar_callback:

            ttk.Button(
                botoes,
                text="DIGITALIZAR",
                command=lambda: escolher(
                    "digitalizar"
                ),
                style="PrinterView.Report.TButton",
            ).pack(
                side="right",
                padx=(8, 0),
            )

        if texto is not None:

            ttk.Button(
                botoes,
                text="VISUALIZAR",
                command=lambda: escolher(
                    "visualizar"
                ),
                style="PrinterView.Report.TButton",
            ).pack(
                side="right",
                padx=(8, 0),
            )

        self.wait_window(
            dialogo
        )

        acao = resultado[
            "acao"
        ]

        if acao == "visualizar":

            if texto is not None:

                self._abrir_preview(
                    titulo,
                    texto,
                    imprimir_callback,
                )

        elif acao == "digitalizar":

            if digitalizar_callback:

                try:

                    digitalizar_callback()

                except ReportError as erro:

                    messagebox.showerror(
                        "Digitalização",
                        str(erro),
                        parent=self,
                    )

                except Exception as erro:

                    messagebox.showerror(
                        "Digitalização",
                        (
                            "Não foi possível gerar "
                            "o relatório digital.\n\n"
                            f"{erro}"
                        ),
                        parent=self,
                    )

        elif acao == "imprimir":

            if imprimir_callback:

                try:

                    imprimir_callback()

                except ReportError as erro:

                    messagebox.showerror(
                        "Impressão",
                        str(erro),
                        parent=self,
                    )

                except Exception as erro:

                    messagebox.showerror(
                        "Impressão",
                        (
                            "Não foi possível imprimir "
                            "o relatório.\n\n"
                            f"{erro}"
                        ),
                        parent=self,
                    )

        return acao

    # ========================================================
    # PREVIEW
    # ========================================================

    def _abrir_preview(
        self,
        titulo,
        texto,
        imprimir_callback=None,
    ):

        preview = tk.Toplevel(
            self.winfo_toplevel()
        )

        preview.title(
            f"Visualização — {titulo}"
        )

        preview.geometry(
            "900x700"
        )

        preview.minsize(
            700,
            500,
        )

        preview.transient(
            self.winfo_toplevel()
        )

        preview.configure(
            background=self.COR_FUNDO
        )

        preview.columnconfigure(
            0,
            weight=1,
        )

        preview.rowconfigure(
            1,
            weight=1,
        )

        header = tk.Frame(
            preview,
            background=self.COR_FUNDO,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=15,
        )

        header.columnconfigure(
            0,
            weight=1,
        )

        tk.Label(
            header,
            text=titulo,
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        tk.Label(
            header,
            text="Visualização do relatório",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(3, 0),
        )

        corpo = tk.Frame(
            preview,
            background=self.COR_PAINEL,
            highlightbackground=self.COR_BORDA,
            highlightthickness=1,
        )

        corpo.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 10),
        )

        corpo.columnconfigure(
            0,
            weight=1,
        )

        corpo.rowconfigure(
            0,
            weight=1,
        )

        texto_widget = tk.Text(
            corpo,
            wrap="none",
            font=("Consolas", 10),
            background=self.COR_PAINEL,
            foreground=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            selectbackground=self.COR_SELECAO,
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=15,
            undo=False,
        )

        texto_widget.insert(
            "1.0",
            str(texto),
        )

        texto_widget.configure(
            state="disabled"
        )

        scrollbar_vertical = ttk.Scrollbar(
            corpo,
            orient="vertical",
            command=texto_widget.yview,
            style="PrinterView.Vertical.TScrollbar",
        )

        scrollbar_horizontal = ttk.Scrollbar(
            corpo,
            orient="horizontal",
            command=texto_widget.xview,
        )

        texto_widget.configure(
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set,
        )

        texto_widget.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar_vertical.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        scrollbar_horizontal.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        footer = tk.Frame(
            preview,
            background=self.COR_FUNDO,
        )

        footer.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 18),
        )

        footer.columnconfigure(
            0,
            weight=1,
        )

        tk.Label(
            footer,
            text=(
                "O conteúdo acima será utilizado "
                "como referência para a impressão."
            ),
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        botoes = tk.Frame(
            footer,
            background=self.COR_FUNDO,
        )

        botoes.grid(
            row=0,
            column=1,
            sticky="e",
        )

        ttk.Button(
            botoes,
            text="FECHAR",
            command=preview.destroy,
            style="PrinterView.TButton",
        ).pack(
            side="left",
            padx=(0, 8),
        )

        if imprimir_callback:

            ttk.Button(
                botoes,
                text="IMPRIMIR",
                command=lambda: (
                    self._imprimir_do_preview(
                        preview,
                        imprimir_callback,
                    )
                ),
                style="PrinterView.Report.TButton",
            ).pack(
                side="left",
            )

        preview.focus_set()

    # ========================================================
    # IMPRIMIR A PARTIR DO PREVIEW
    # ========================================================

    def _imprimir_do_preview(
        self,
        preview,
        imprimir_callback,
    ):

        try:

            imprimir_callback()

            preview.destroy()

        except Exception as erro:

            messagebox.showerror(
                "Impressão",
                (
                    "Não foi possível imprimir "
                    "o relatório.\n\n"
                    f"{erro}"
                ),
                parent=preview,
            )

    # ========================================================
    # RELATÓRIO DE ATIVO
    # ========================================================

    def _clicar_relatorio_ativo(
        self,
    ):

        try:

            service = (
                self._criar_report_service()
            )

            resultado = (
                service.preparar_ativo()
                if hasattr(
                    service,
                    "preparar_ativo",
                )
                else None
            )

            if resultado is not None:

                if not isinstance(
                    resultado,
                    dict,
                ):

                    raise ReportError(
                        "O ReportService retornou "
                        "um resultado inválido para "
                        "o Relatório de Ativo."
                    )

                texto = resultado.get(
                    "texto",
                    "",
                )

                def imprimir():

                    retorno = (
                        service.imprimir_ativo()
                    )

                    destino = (
                        retorno.get(
                            "destino",
                            "Impressora",
                        )
                        if isinstance(
                            retorno,
                            dict,
                        )
                        else "Impressora"
                    )

                self._escolher_acao_relatorio(
                    "RELATÓRIO DE ATIVO",
                    texto=texto,
                    imprimir_callback=imprimir,
                )

                return

            retorno = service.imprimir_ativo()

            destino = (
                retorno.get(
                    "destino",
                    "Impressora",
                )
                if isinstance(
                    retorno,
                    dict,
                )
                else "Impressora"
            )

        except ReportError as erro:

            messagebox.showerror(
                "Relatório de Ativo",
                str(erro),
                parent=self,
            )

        except Exception as erro:

            messagebox.showerror(
                "Relatório de Ativo",
                (
                    "Ocorreu um erro ao processar "
                    "o Relatório de Ativo.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

    # ========================================================
    # DEMONSTRAÇÃO (VIA RAW 9100 E PCL)
    # ========================================================

    def _clicar_demonstracao(self):
        self.btn_demonstracao.config(text="Enviando...", state="disabled")
        self.update_idletasks()

        def tarefa_demo():
            try:
                from reports.demonstracao import imprimir_relatorio_demonstracao
                
                CAMINHO_IMAGEM_DEMO = r"C:\PrinterAssistant\assets\print\too_dark\check_1.jpg"

                imprimir_relatorio_demonstracao(
                    device=self.device, 
                    imagem=CAMINHO_IMAGEM_DEMO
                )
                
                def sucesso():
                    messagebox.showinfo(
                        "Demonstração", 
                        "Página de demonstração enviada para a impressora com sucesso!", 
                        parent=self
                    )
                    self.btn_demonstracao.config(text="DEMONSTRAÇÃO", state="normal")
                
                if self.winfo_exists():
                    self.after(0, sucesso)

            except Exception as e:
                def erro():
                    messagebox.showerror(
                        "Erro", 
                        f"Falha ao enviar a demonstração para a impressora:\n\n{e}", 
                        parent=self
                    )
                    self.btn_demonstracao.config(text="DEMONSTRAÇÃO", state="normal")
                
                if self.winfo_exists():
                    self.after(0, erro)

        threading.Thread(target=tarefa_demo, daemon=True).start()

    # ========================================================
    # RMA
    # ========================================================

    def _clicar_relatorio_rma(
        self,
    ):
        rma_t0 = time.perf_counter()

        def rma_tempo(etapa):
            print(
                f"[RMA-TIMER] "
                f"{time.perf_counter() - rma_t0:8.3f}s | "
                f"{etapa}",
                flush=True,
            )

        rma_tempo(
            "ENTROU EM _clicar_relatorio_rma"
        )

        if self.device is None:

            messagebox.showerror(
                "Relatório RMA",
                (
                    "Nenhuma UST está selecionada."
                ),
                parent=self,
            )

            return

        try:

            rma_tempo(
                "ANTES DO IMPORT reports.rma"
            )

            from reports.rma import (
                RMAError,
                preparar_rma,
                gerar_etiqueta_rma,
                imprimir_tspl,
            )

            rma_tempo(
                "DEPOIS DO IMPORT reports.rma"
            )

        except ImportError as erro:

            messagebox.showerror(
                "Relatório RMA",
                (
                    "O módulo de RMA não foi encontrado.\n\n"
                    "Arquivo esperado:\n"
                    "reports/rma.py\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

            return

        try:

            rma_tempo(
                "ANTES DA PRIMEIRA preparar_rma (validação)"
            )

            dados_rma = preparar_rma(
                device=self.device,
                fabricante="LEXMARK",
                lote="",
            )

            rma_tempo(
                "DEPOIS DA PRIMEIRA preparar_rma (validação)"
            )

        except RMAError as erro:

            messagebox.showerror(
                "Relatório RMA",
                str(erro),
                parent=self,
            )

            return

        except Exception as erro:

            messagebox.showerror(
                "Relatório RMA",
                (
                    "Não foi possível preparar "
                    "o Relatório RMA.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

            return

        dialogo = tk.Toplevel(
            self.winfo_toplevel()
        )

        rma_tempo(
            "JANELA RMA CRIADA"
        )

        dialogo.title(
            "RELATÓRIO RMA"
        )

        dialogo.geometry(
            "480x420"
        )

        dialogo.minsize(
            440,
            390,
        )

        dialogo.resizable(
            False,
            False,
        )

        dialogo.transient(
            self.winfo_toplevel()
        )

        dialogo.grab_set()

        dialogo.configure(
            background=self.COR_FUNDO
        )

        dialogo.columnconfigure(
            0,
            weight=1,
        )

        frame = tk.Frame(
            dialogo,
            background=self.COR_FUNDO,
            padx=25,
            pady=22,
        )

        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        frame.columnconfigure(
            1,
            weight=1,
        )

        tk.Label(
            frame,
            text="RELATÓRIO RMA",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 4),
        )

        tk.Label(
            frame,
            text=(
                "Etiqueta da unidade de imagem"
            ),
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            anchor="w",
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 18),
        )

        tk.Label(
            frame,
            text="SERIAL",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=5,
        )

        serial_widget = tk.Text(
            frame,
            height=1,
            font=("Segoe UI", 10, "bold"),
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=5,
        )

        serial_widget.insert(
            "1.0",
            str(
                dados_rma["serial"]
            ),
        )

        serial_widget.configure(
            state="disabled"
        )

        serial_widget.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=5,
        )

        tk.Label(
            frame,
            text="NÍVEL",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=5,
        )

        tk.Label(
            frame,
            text=(
                f'{dados_rma["nivel"]:.0f}%'
            ),
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=8,
            pady=5,
        ).grid(
            row=3,
            column=1,
            sticky="ew",
            pady=5,
        )

        tk.Label(
            frame,
            text="FABRICANTE",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=5,
        )

        fabricante_var = tk.StringVar(
            value="LEXMARK"
        )

        fabricante_combo = ttk.Combobox(
            frame,
            textvariable=fabricante_var,
            values=(
                "LEXMARK",
                "GLOBAL",
            ),
            state="readonly",
            font=("Segoe UI", 10),
            style="PrinterView.RMA.TCombobox",
        )

        fabricante_combo.grid(
            row=4,
            column=1,
            sticky="ew",
            pady=5,
        )

        starter_detectado = bool(
            dados_rma.get("started", False)
        )

        starter_texto = dados_rma.get(
            "starter_texto",
            "SIM" if starter_detectado else "NAO",
        )

        tk.Label(
            frame,
            text="STARTER",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=5,
            column=0,
            sticky="w",
            pady=5,
        )

        tk.Label(
            frame,
            text=starter_texto,
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=8,
            pady=5,
        ).grid(
            row=5,
            column=1,
            sticky="ew",
            pady=5,
        )

        tk.Label(
            frame,
            text="LOTE",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(
            row=6,
            column=0,
            sticky="w",
            pady=5,
        )

        lote_var = tk.StringVar(
            value=""
        )

        lote_entry = tk.Entry(
            frame,
            textvariable=lote_var,
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief="flat",
            font=("Segoe UI", 10),
        )

        lote_entry.grid(
            row=6,
            column=1,
            sticky="ew",
            pady=5,
        )

        tk.Label(
            frame,
            text=(
                "A etiqueta será impressa em:\n"
                "TSC 192.168.14.151:9100\n"
                "100 x 150 mm    •    GAP 2 mm"
            ),
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 8),
            justify="left",
            anchor="w",
        ).grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(18, 10),
        )

        resultado = {
            "acao": None,
            "dados": None,
        }

        def preparar():

            rma_tempo(
                "ANTES DA SEGUNDA preparar_rma (botão escolhido)"
            )

            fabricante = (
                fabricante_var.get().strip()
            )

            lote = (
                lote_var.get().strip()
            )

            try:

                dados = preparar_rma(
                    device=self.device,
                    fabricante=fabricante,
                    lote=lote,
                )

                rma_tempo(
                    "DEPOIS DA SEGUNDA preparar_rma (botão escolhido)"
                )

            except RMAError as erro:

                messagebox.showerror(
                    "Relatório RMA",
                    str(erro),
                    parent=dialogo,
                )

                return None

            except Exception as erro:

                messagebox.showerror(
                    "Relatório RMA",
                    (
                        "Erro ao preparar "
                        "a etiqueta RMA.\n\n"
                        f"{erro}"
                    ),
                    parent=dialogo,
                )

                return None

            return dados

        botoes = tk.Frame(
            frame,
            background=self.COR_FUNDO,
        )

        botoes.grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )

        botoes.columnconfigure(
            0,
            weight=1,
        )

        def cancelar():

            dialogo.destroy()

        def visualizar():

            rma_tempo(
                "CLIQUE EM VISUALIZAR"
            )

            dados = preparar()

            if dados is None:
                return

            resultado["acao"] = "visualizar"
            resultado["dados"] = dados

            dialogo.destroy()

        def imprimir():

            rma_tempo(
                "CLIQUE EM IMPRIMIR NA JANELA RMA"
            )

            dados = preparar()

            if dados is None:
                return

            resultado["acao"] = "imprimir"
            resultado["dados"] = dados

            dialogo.destroy()

        ttk.Button(
            botoes,
            text="CANCELAR",
            command=cancelar,
            style="PrinterView.TButton",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            botoes,
            text="VISUALIZAR",
            command=visualizar,
            style="PrinterView.Report.TButton",
        ).grid(
            row=0,
            column=1,
            padx=(8, 0),
        )

        ttk.Button(
            botoes,
            text="IMPRIMIR",
            command=imprimir,
            style="PrinterView.RMA.TButton",
        ).grid(
            row=0,
            column=2,
            padx=(8, 0),
        )

        lote_entry.focus_set()

        rma_tempo(
            "ANTES DO wait_window — AGUARDANDO AÇÃO DO USUÁRIO"
        )

        self.wait_window(
            dialogo
        )

        rma_tempo(
            "DEPOIS DO wait_window — JANELA RMA FECHOU"
        )

        acao = resultado[
            "acao"
        ]

        dados = resultado[
            "dados"
        ]

        if not acao or dados is None:
            return

        try:

            rma_tempo(
                "ANTES DE gerar_etiqueta_rma"
            )

            tspl = gerar_etiqueta_rma(
                serial=dados["serial"],
                fabricante=dados["fabricante"],
                started=dados["started"],
                nivel=dados["nivel"],
                lote=dados["lote"],
            )

            rma_tempo(
                "DEPOIS DE gerar_etiqueta_rma"
            )

        except RMAError as erro:

            messagebox.showerror(
                "Relatório RMA",
                str(erro),
                parent=self,
            )

            return

        except Exception as erro:

            messagebox.showerror(
                "Relatório RMA",
                (
                    "Não foi possível gerar "
                    "a etiqueta RMA.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

            return

        if acao == "visualizar":

            texto = (
                "PRINTER ASSISTANT\n"
                "RELATÓRIO RMA\n"
                "\n"
                "----------------------------------------\n"
                f"SERIAL: {dados['serial']}\n"
                f"FABRICANTE: {dados['fabricante']}\n"
                f"STARTER: {dados.get('starter_texto', 'SIM' if dados['started'] else 'NAO')}\n"
                f"DEFEITO: {dados['defeito']}\n"
                f"NIVEL: {dados['nivel']:.0f}%\n"
                "LOTE: ____________________\n"
                "----------------------------------------\n"
                "\n"
                "CÓDIGO DE BARRAS\n"
                f"CODE 128: {dados['serial']}\n"
                "\n"
                "DESTINO:\n"
                "TSC\n"
                "192.168.14.151:9100\n"
                "\n"
                "MÍDIA:\n"
                "100 x 150 mm\n"
                "GAP 2 mm\n"
                "\n"
                "A etiqueta será enviada diretamente "
                "para a TSC.\n"
                "\n"
                "Nenhuma nova coleta será realizada."
            )

            def imprimir_preview_rma():

                rma_tempo(
                    "CLIQUE EM IMPRIMIR NO PREVIEW RMA"
                )

                rma_tempo(
                    "ANTES DE imprimir_tspl (PREVIEW)"
                )

                try:

                    imprimir_tspl(
                        tspl
                    )

                    rma_tempo(
                        "DEPOIS DE imprimir_tspl (PREVIEW) — ETIQUETA ENVIADA"
                    )

                except RMAError as erro:

                    raise erro

                except Exception as erro:

                    raise RMAError(
                        "Não foi possível "
                        "imprimir a etiqueta RMA.\n\n"
                        f"{erro}"
                    ) from erro

            rma_tempo(
                "ANTES DE ABRIR PREVIEW RMA"
            )

            self._abrir_preview(
                "RELATÓRIO RMA",
                texto,
                imprimir_callback=imprimir_preview_rma,
            )

            return

        if acao == "imprimir":

            try:

                rma_tempo(
                    "ANTES DE imprimir_tspl (DIRETO)"
                )

                imprimir_tspl(
                    tspl
                )

                rma_tempo(
                    "DEPOIS DE imprimir_tspl (DIRETO) — ETIQUETA ENVIADA"
                )

            except RMAError as erro:

                messagebox.showerror(
                    "Relatório RMA",
                    str(erro),
                    parent=self,
                )

                return

            except Exception as erro:

                messagebox.showerror(
                    "Relatório RMA",
                    (
                        "Não foi possível "
                        "imprimir a etiqueta RMA.\n\n"
                        f"{erro}"
                    ),
                    parent=self,
                )

                return

    # ========================================================
    # PRODUÇÃO DE ETIQUETAS
    # ========================================================

    def _abrir_producao_etiqueta(self):
        try:
            from reports import producao_etiqueta
        except ImportError as erro:
            messagebox.showerror(
                "Produção de Etiquetas",
                f"Não foi possível carregar o módulo 'reports.producao_etiqueta'.\n\n{erro}",
                parent=self,
            )
            return

        dialogo = tk.Toplevel(self.winfo_toplevel())
        dialogo.title("PRODUÇÃO DE ETIQUETAS")
        dialogo.geometry("540x480")
        dialogo.minsize(500, 450)
        dialogo.resizable(False, False)
        dialogo.transient(self.winfo_toplevel())
        dialogo.grab_set()
        dialogo.configure(background=self.COR_FUNDO)

        frame = tk.Frame(dialogo, background=self.COR_FUNDO, padx=25, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="PRODUÇÃO DE ETIQUETAS",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 2))

        lbl_status = tk.Label(
            frame,
            text="Selecione o consumível, fabricante e emita a etiqueta.",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_status.pack(anchor="w", pady=(0, 14))

        campos_frame = tk.Frame(frame, background=self.COR_FUNDO)
        campos_frame.pack(fill="x", pady=5)
        campos_frame.columnconfigure(1, weight=1)

        seriais_coletados = {"toner": "", "unidade_imagem": ""}

        def _extrair_seriais():
            nonlocal seriais_coletados
            novos = {"toner": "", "unidade_imagem": ""}
            if self.device:
                try:
                    dados_dev = self.device.to_dict() if hasattr(self.device, "to_dict") else {}
                    ident_dict = dados_dev.get("identificacao", {}) or {}
                    serial_impressora = str(
                        ident_dict.get("serial")
                        or ident_dict.get("numero_serie")
                        or (self.device.serial() if callable(getattr(self.device, "serial", None)) else getattr(self.device, "serial", ""))
                        or ""
                    ).strip()

                    def _serial_suprimento_valido(val):
                        if not val:
                            return ""
                        s_limpo = str(val).strip()
                        if s_limpo.lower() in ("none", "desconhecido", "n/d", "n/a", "null", ""):
                            return ""
                        if serial_impressora and s_limpo.upper() == serial_impressora.upper():
                            return ""
                        return s_limpo

                    supplies = dados_dev.get("supplies", []) or []

                    for item in supplies:
                        if isinstance(item, dict):
                            t = self._tipo_consumivel(item)
                            s = _serial_suprimento_valido(
                                item.get("numero_serie")
                                or item.get("serial")
                                or item.get("serial_number")
                                or item.get("serialNumber")
                                or item.get("numeroSerie")
                                or ""
                            )
                            if not t:
                                nome_item = str(
                                    item.get("nome")
                                    or item.get("name")
                                    or item.get("descricao")
                                    or item.get("description")
                                    or ""
                                ).lower()
                                if "toner" in nome_item or "cartucho" in nome_item or "cartridge" in nome_item:
                                    t = "toner"
                                elif "imagem" in nome_item or "imaging" in nome_item or "drum" in nome_item or "fotocondutor" in nome_item or "photoconductor" in nome_item:
                                    t = "unidade_imagem"

                            if t in novos and s and not novos[t]:
                                novos[t] = s

                    for attr in ["toner_serial", "serial_toner", "cartridge_serial"]:
                        if hasattr(self.device, attr) and getattr(self.device, attr):
                            val_attr = _serial_suprimento_valido(getattr(self.device, attr))
                            if val_attr and not novos["toner"]:
                                novos["toner"] = val_attr
                    for attr in ["drum_serial", "serial_drum", "imaging_serial", "unidade_imagem_serial"]:
                        if hasattr(self.device, attr) and getattr(self.device, attr):
                            val_attr = _serial_suprimento_valido(getattr(self.device, attr))
                            if val_attr and not novos["unidade_imagem"]:
                                novos["unidade_imagem"] = val_attr

                except Exception as e:
                    print(f"[ERRO EXTRAIR SERIAIS] {e}")
            seriais_coletados = novos

        _extrair_seriais()

        tk.Label(campos_frame, text="CONSUMÍVEL", background=self.COR_FUNDO, foreground=self.COR_TEXTO_SECUNDARIO, font=("Segoe UI", 8, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=6, padx=(0, 10))
        tipo_var = tk.StringVar(value="Cartucho de Toner")
        tipo_combo = ttk.Combobox(campos_frame, textvariable=tipo_var, values=("Cartucho de Toner", "Unidade de Imagem"), state="readonly", font=("Segoe UI", 10), style="PrinterView.RMA.TCombobox")
        tipo_combo.grid(row=0, column=1, sticky="ew", pady=6)

        tk.Label(campos_frame, text="FABRICANTE", background=self.COR_FUNDO, foreground=self.COR_TEXTO_SECUNDARIO, font=("Segoe UI", 8, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=6, padx=(0, 10))
        fabricante_var = tk.StringVar(value="REM")
        fabricante_combo = ttk.Combobox(campos_frame, textvariable=fabricante_var, values=("REM", "LEXMARK", "GLOBAL", "3I", "VRI"), state="readonly", font=("Segoe UI", 10), style="PrinterView.RMA.TCombobox")
        fabricante_combo.grid(row=1, column=1, sticky="ew", pady=6)

        tk.Label(campos_frame, text="SERIAL", background=self.COR_FUNDO, foreground=self.COR_TEXTO_SECUNDARIO, font=("Segoe UI", 8, "bold"), anchor="w").grid(row=2, column=0, sticky="w", pady=6, padx=(0, 10))
        serial_var = tk.StringVar()
        serial_entry = tk.Entry(campos_frame, textvariable=serial_var, background=self.COR_PAINEL_2, foreground=self.COR_TEXTO, insertbackground=self.COR_TEXTO, relief="flat", font=("Segoe UI", 10, "bold"))
        serial_entry.grid(row=2, column=1, sticky="ew", pady=6)

        def _ao_mudar_tipo(event=None):
            tipo_sel = tipo_var.get()
            if tipo_sel == "Cartucho de Toner":
                serial_var.set(seriais_coletados.get("toner", ""))
            else:
                serial_var.set(seriais_coletados.get("unidade_imagem", ""))

        tipo_combo.bind("<<ComboboxSelected>>", _ao_mudar_tipo)
        _ao_mudar_tipo()

        tsc_ip = getattr(producao_etiqueta, "TSC_IP", getattr(producao_etiqueta, "PRODUCAO_IP_PADRAO", "192.168.14.111"))
        try:
            if hasattr(producao_etiqueta, "resolver_ip"):
                tsc_ip = producao_etiqueta.resolver_ip(tsc_ip, tipo="producao")
        except Exception:
            pass
        tsc_porta = getattr(producao_etiqueta, "TSC_PORTA", getattr(producao_etiqueta, "PRODUCAO_PORTA_PADRAO", 9100))

        tk.Label(frame, text=f"Destino da impressão: TSC {tsc_ip}:{tsc_porta}", background=self.COR_FUNDO, foreground=self.COR_TEXTO_FRACO, font=("Segoe UI", 8), justify="left", anchor="w").pack(anchor="w", pady=(10, 15))

        botoes_topo = tk.Frame(frame, background=self.COR_FUNDO)
        botoes_topo.pack(fill="x", pady=(0, 10))

        btn_atualizar_coleta = ttk.Button(botoes_topo, text="🔄 Atualizar Coleta", style="PrinterView.TButton")

        def carregar_dados_impressora():
            btn_atualizar_coleta.config(text="Atualizando...", state="disabled")
            lbl_status.config(foreground=self.COR_ATENCAO, text="Coletando PJL + SYSDEBUG + SNMP... aguarde.")
            dialogo.update_idletasks()

            def tarefa_atualizacao():
                try:
                    import asyncio
                    if self.device is None:
                        raise RuntimeError("Nenhuma impressora selecionada.")

                    if hasattr(self.device, "coletar") and callable(self.device.coletar):
                        coro = self.device.coletar()
                        if inspect.isawaitable(coro):
                            asyncio.run(coro)
                    elif hasattr(self.device, "coletar_dados"):
                        self.device.coletar_dados()
                    elif hasattr(self.device, "atualizar_dados"):
                        self.device.atualizar_dados()

                    def atualizar_ui_sucesso():
                        if self.winfo_exists():
                            self.atualizar(self.device)
                            toplevel = self.winfo_toplevel()
                            if hasattr(toplevel, "lbl_status"):
                                try:
                                    toplevel.lbl_status.config(text="Coleta concluída.")
                                except Exception:
                                    pass
                        if not dialogo.winfo_exists():
                            return
                        _extrair_seriais()
                        _ao_mudar_tipo()
                        lbl_status.config(foreground=self.COR_ONLINE, text="Dados atualizados e sincronizados com sucesso!")
                        btn_atualizar_coleta.config(text="🔄 Atualizar Coleta", state="normal")

                    if self.winfo_exists():
                        self.after(0, atualizar_ui_sucesso)

                except Exception as erro:
                    def atualizar_ui_erro():
                        if not dialogo.winfo_exists():
                            return
                        lbl_status.config(foreground=self.COR_OFFLINE, text="Erro ao atualizar coleta.")
                        btn_atualizar_coleta.config(text="🔄 Atualizar Coleta", state="normal")
                        messagebox.showerror("Erro", f"Falha na atualização:\n{erro}", parent=dialogo)

                    if self.winfo_exists():
                        self.after(0, atualizar_ui_erro)

            threading.Thread(target=tarefa_atualizacao, daemon=True).start()

        btn_atualizar_coleta.config(command=carregar_dados_impressora)
        btn_atualizar_coleta.pack(side="left")

        btn_demonstracao = ttk.Button(botoes_topo, text="Demonstração", style="PrinterView.TButton")

        def acionar_demonstracao_producao():
            btn_demonstracao.config(text="Enviando...", state="disabled")
            dialogo.update_idletasks()

            def tarefa_demo():
                try:
                    from reports.demonstracao import imprimir_relatorio_demonstracao
                    
                    CAMINHO_IMAGEM_DEMO = r"C:\PrinterAssistant\assets\print\too_dark\check_1.jpg"

                    imprimir_relatorio_demonstracao(
                        device=self.device, 
                        imagem=CAMINHO_IMAGEM_DEMO
                    )
                    
                    def sucesso():
                        messagebox.showinfo(
                            "Demonstração", 
                            "Página de demonstração enviada para a impressora com sucesso!", 
                            parent=dialogo
                        )
                        btn_demonstracao.config(text="Demonstração", state="normal")
                    
                    if dialogo.winfo_exists():
                        dialogo.after(0, sucesso)

                except Exception as e:
                    def erro():
                        messagebox.showerror(
                            "Erro", 
                            f"Falha ao enviar a demonstração para a impressora:\n\n{e}", 
                            parent=dialogo
                        )
                        btn_demonstracao.config(text="Demonstração", state="normal")
                    
                    if dialogo.winfo_exists():
                        dialogo.after(0, erro)

            threading.Thread(target=tarefa_demo, daemon=True).start()

        btn_demonstracao.config(command=acionar_demonstracao_producao)
        btn_demonstracao.pack(side="right")
        fabricante_combo.focus_set()

        botoes_rodape = tk.Frame(frame, background=self.COR_FUNDO)
        botoes_rodape.pack(fill="x", side="bottom", pady=(6, 0))

        ttk.Separator(frame, orient="horizontal").pack(fill="x", side="bottom", pady=12)

        btn_cancelar = ttk.Button(
            botoes_rodape,
            text="FECHAR",
            style="PrinterView.TButton",
            command=dialogo.destroy
        )
        btn_cancelar.pack(side="left")

        btn_imprimir_etiqueta = ttk.Button(
            botoes_rodape,
            text="IMPRIMIR ETIQUETA",
            style="PrinterView.Producao.TButton"
        )
        btn_imprimir_etiqueta.pack(side="right")

        def acionar_imprimir_etiqueta():
            tipo_sel = tipo_var.get().strip()
            fab_sel = fabricante_var.get().strip()
            ser_sel = serial_var.get().strip()

            if not ser_sel:
                messagebox.showwarning("Aviso", "O campo SERIAL não pode estar vazio.", parent=dialogo)
                serial_entry.focus_set()
                return

            modelo_maquina = "MX611"
            if self.device:
                try:
                    dados_dev = self.device.to_dict() if hasattr(self.device, "to_dict") else {}
                    ident = dados_dev.get("identificacao", {}) or {}
                    mod_dev = ident.get("modelo") or (
                        self.device.modelo() if callable(getattr(self.device, "modelo", None)) else getattr(self.device, "modelo", "")
                    )
                    if mod_dev and str(mod_dev).strip().lower() not in ("desconhecido", "none", ""):
                        modelo_maquina = str(mod_dev).strip()
                except Exception:
                    pass

            btn_imprimir_etiqueta.config(text="Enviando...", state="disabled")
            dialogo.update_idletasks()

            def tarefa_imprimir():
                try:
                    if hasattr(producao_etiqueta, 'gerar_tspl'):
                        tspl = producao_etiqueta.gerar_tspl(
                            serial=ser_sel,
                            fabricante=fab_sel,
                            tipo=tipo_sel,
                            modelo=modelo_maquina,
                            device=self.device,
                        )
                    elif hasattr(producao_etiqueta, 'gerar_etiqueta'):
                        tspl = producao_etiqueta.gerar_etiqueta(
                            serial=ser_sel,
                            fabricante=fab_sel,
                            tipo=tipo_sel,
                            modelo=modelo_maquina,
                            device=self.device,
                        )
                    else:
                        raise Exception("A função de gerar etiqueta ('gerar_etiqueta' ou 'gerar_tspl') não foi encontrada no módulo 'producao_etiqueta'.")

                    if hasattr(producao_etiqueta, 'imprimir_tspl'):
                        producao_etiqueta.imprimir_tspl(tspl)
                    else:
                        import socket
                        ip = getattr(producao_etiqueta, "TSC_IP", "192.168.14.151")
                        porta = getattr(producao_etiqueta, "TSC_PORTA", 9100)
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(5)
                            s.connect((ip, porta))
                            s.sendall(tspl.encode('utf-8') if isinstance(tspl, str) else tspl)

                    def sucesso():
                        messagebox.showinfo("Sucesso", "Etiqueta enviada para a impressora TSC com sucesso!", parent=dialogo)
                        btn_imprimir_etiqueta.config(text="IMPRIMIR ETIQUETA", state="normal")

                    if dialogo.winfo_exists():
                        dialogo.after(0, sucesso)

                except Exception as e:
                    def erro():
                        messagebox.showerror("Erro", f"Falha ao imprimir a etiqueta:\n\n{e}", parent=dialogo)
                        btn_imprimir_etiqueta.config(text="IMPRIMIR ETIQUETA", state="normal")

                    if dialogo.winfo_exists():
                        dialogo.after(0, erro)

            threading.Thread(target=tarefa_imprimir, daemon=True).start()

        btn_imprimir_etiqueta.config(command=acionar_imprimir_etiqueta)

    # ========================================================
    # ATUALIZAR
    # ========================================================

    def _clicar_atualizar(
        self,
    ):

        if self.on_refresh:
            self.on_refresh()

        else:
            self.atualizar()

    # ========================================================
    # VOLTAR
    # ========================================================

    def _clicar_voltar(
        self,
    ):

        if self.on_back:
            self.on_back()