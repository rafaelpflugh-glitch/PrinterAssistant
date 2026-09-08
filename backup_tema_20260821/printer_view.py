# ============================================================
# PRINTER ASSISTANT
# INTERFACE - PRINTER VIEW
# ============================================================
#
# Ficha visual da impressora.
#
# Responsabilidades:
#
#   - apresentar os dados já coletados pelo PrinterDevice;
#   - apresentar consumíveis;
#   - apresentar conectividade;
#   - disponibilizar os relatórios;
#   - solicitar atualização através do callback recebido;
#
# Esta classe NÃO realiza comunicação de rede diretamente.
#
# A comunicação dos relatórios é feita através de:
#
#       services.report_service.ReportService
#
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from services.report_service import (
    ReportError,
    ReportService,
)


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
        - Garantia somente para unidade de imagem.
        - Origem do contador não é exibida.
        - Informações textuais são selecionáveis.
        - Relatórios são acionados pelo ReportService.
    """

    # =========================================================
    # CORES
    # =========================================================

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

    # =========================================================
    # INICIALIZAÇÃO
    # =========================================================

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

    # =========================================================
    # ESTILOS
    # =========================================================

    def _criar_estilos(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # -----------------------------------------------------
        # FRAME PRINCIPAL
        # -----------------------------------------------------

        style.configure(
            "PrinterView.TFrame",
            background=self.COR_FUNDO,
        )

        # -----------------------------------------------------
        # LABEL
        # -----------------------------------------------------

        style.configure(
            "PrinterView.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=(
                "Segoe UI",
                10,
            ),
        )

        style.configure(
            "PrinterView.Secondary.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=(
                "Segoe UI",
                9,
            ),
        )

        style.configure(
            "PrinterView.Title.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=(
                "Segoe UI",
                17,
                "bold",
            ),
        )

        style.configure(
            "PrinterView.Model.TLabel",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO,
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
        )

        style.configure(
            "PrinterView.Section.TLabel",
            background=self.COR_PAINEL,
            foreground=self.COR_TEXTO,
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
        )

        style.configure(
            "PrinterView.FieldTitle.TLabel",
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=(
                "Segoe UI",
                8,
            ),
        )

        style.configure(
            "PrinterView.FieldValue.TLabel",
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        )

        style.configure(
            "PrinterView.Serial.TLabel",
            background=self.COR_PAINEL_2,
            foreground=self.COR_TEXTO,
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
        )

        # -----------------------------------------------------
        # LABEL FRAME
        # -----------------------------------------------------

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
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        )

        # -----------------------------------------------------
        # BOTÕES
        # -----------------------------------------------------

        style.configure(
            "PrinterView.TButton",
            background="#252a2f",
            foreground=self.COR_TEXTO,
            bordercolor=self.COR_BORDA,
            lightcolor="#252a2f",
            darkcolor="#252a2f",
            padding=8,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        )

        style.map(
            "PrinterView.TButton",
            background=[
                (
                    "active",
                    "#30373d",
                ),
                (
                    "pressed",
                    "#20252a",
                ),
                (
                    "disabled",
                    "#191c1f",
                ),
            ],
            foreground=[
                (
                    "disabled",
                    "#5f666d",
                ),
            ],
        )

        style.configure(
            "PrinterView.Report.TButton",
            background="#20262b",
            foreground=self.COR_TEXTO,
            bordercolor="#3a434a",
            lightcolor="#20262b",
            darkcolor="#20262b",
            padding=10,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        )

        style.map(
            "PrinterView.Report.TButton",
            background=[
                (
                    "active",
                    "#2b3942",
                ),
                (
                    "pressed",
                    "#1b2227",
                ),
                (
                    "disabled",
                    "#191c1f",
                ),
            ],
        )

        # -----------------------------------------------------
        # PROGRESSBAR
        # -----------------------------------------------------

        style.configure(
            "PrinterView.Horizontal.TProgressbar",
            troughcolor="#292e33",
            background=self.COR_DESTAQUE,
            bordercolor="#292e33",
            lightcolor=self.COR_DESTAQUE,
            darkcolor=self.COR_DESTAQUE,
            thickness=8,
        )

        # -----------------------------------------------------
        # SCROLLBAR
        # -----------------------------------------------------

        style.configure(
            "PrinterView.Vertical.TScrollbar",
            background="#252a2f",
            troughcolor=self.COR_FUNDO,
            bordercolor=self.COR_FUNDO,
            arrowcolor="#8b9299",
        )

    # =========================================================
    # TEXTO SELECIONÁVEL
    # =========================================================

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

            font = (
                "Segoe UI",
                10,
            )

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
            state="disabled",
        )

        return widget

    # =========================================================
    # DEFINIR TEXTO
    # =========================================================

    def _definir_texto(
        self,
        widget,
        texto,
    ):

        widget.configure(
            state="normal",
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
            state="disabled",
        )

    # =========================================================
    # INTERFACE
    # =========================================================

    def _criar_interface(self):

        # -----------------------------------------------------
        # CONFIGURAÇÃO DA GRADE PRINCIPAL
        # -----------------------------------------------------

        self.columnconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            2,
            weight=1,
        )

        # -----------------------------------------------------
        # CABEÇALHO
        # -----------------------------------------------------

        header = tk.Frame(
            self,
            background=self.COR_FUNDO,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(
                14,
                10,
            ),
        )

        header.columnconfigure(
            0,
            weight=1,
        )

        # -----------------------------------------------------
        # TÍTULO
        # -----------------------------------------------------

        self.lbl_titulo = ttk.Label(
            header,
            text="PRINTER ASSISTANT",
            style="PrinterView.Title.TLabel",
        )

        self.lbl_titulo.grid(
            row=0,
            column=0,
            sticky="w",
        )

        # -----------------------------------------------------
        # ESTADO
        # -----------------------------------------------------

        self.lbl_estado = tk.Label(
            header,
            text="●  OFFLINE",
            background=self.COR_FUNDO,
            foreground=self.COR_OFFLINE,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        )

        self.lbl_estado.grid(
            row=0,
            column=1,
            sticky="e",
        )

        # -----------------------------------------------------
        # MODELO
        # -----------------------------------------------------

        self.lbl_modelo = ttk.Label(
            header,
            text="Impressora",
            style="PrinterView.Model.TLabel",
        )

        self.lbl_modelo.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(
                3,
                0,
            ),
        )

        # -----------------------------------------------------
        # IP
        # -----------------------------------------------------

        self.lbl_ip = ttk.Label(
            header,
            text="",
            style="PrinterView.Secondary.TLabel",
        )

        self.lbl_ip.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(
                1,
                0,
            ),
        )

        # -----------------------------------------------------
        # IDENTIFICAÇÃO
        # -----------------------------------------------------

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
            pady=(
                0,
                10,
            ),
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

        # -----------------------------------------------------
        # ÁREA PRINCIPAL
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # CONSUMÍVEIS
        # -----------------------------------------------------

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
            padx=(
                0,
                6,
            ),
        )

        supplies_frame.columnconfigure(
            0,
            weight=1,
        )

        supplies_frame.rowconfigure(
            0,
            weight=1,
        )

        # -----------------------------------------------------
        # CANVAS
        # -----------------------------------------------------

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
            (
                0,
                0,
            ),
            window=self.supplies_container,
            anchor="nw",
        )

        # -----------------------------------------------------
        # SCROLL REGION
        # -----------------------------------------------------

        def atualizar_scroll(
            event=None,
        ):

            canvas.configure(
                scrollregion=canvas.bbox(
                    "all"
                )
            )

        def ajustar_largura(
            event,
        ):

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

        # -----------------------------------------------------
        # MOUSE WHEEL
        # -----------------------------------------------------

        def mousewheel(
            event,
        ):

            canvas.yview_scroll(
                int(
                    -1
                    * (
                        event.delta
                        / 120
                    )
                ),
                "units",
            )

        def mousewheel_linux_up(
            event,
        ):

            canvas.yview_scroll(
                -1,
                "units",
            )

        def mousewheel_linux_down(
            event,
        ):

            canvas.yview_scroll(
                1,
                "units",
            )

        def ativar_mousewheel(
            event,
        ):

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

        def desativar_mousewheel(
            event,
        ):

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

        # -----------------------------------------------------
        # RELATÓRIOS
        # -----------------------------------------------------

        self.reports_frame = ttk.LabelFrame(
            principal,
            text=" RELATÓRIOS ",
            padding=10,
            style="PrinterView.TLabelframe",
        )

        self.reports_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(
                6,
                0,
            ),
        )

        self.reports_frame.columnconfigure(
            0,
            weight=1,
        )

        self.reports_frame.rowconfigure(
            4,
            weight=1,
        )

        # -----------------------------------------------------
        # BOTÃO ATIVO
        # -----------------------------------------------------

        self.btn_relatorio_ativo = ttk.Button(
            self.reports_frame,
            text=(
                "RELATÓRIO\n"
                "DE ATIVO"
            ),
            command=self._clicar_relatorio_ativo,
            style="PrinterView.Report.TButton",
        )

        self.btn_relatorio_ativo.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(
                4,
                8,
            ),
        )

        # -----------------------------------------------------
        # BOTÃO CONFIGURAÇÃO
        # -----------------------------------------------------

        self.btn_configuracao = ttk.Button(
            self.reports_frame,
            text=(
                "CONFIGURAÇÃO\n"
                "E SUPRIMENTOS"
            ),
            command=self._clicar_configuracao,
            style="PrinterView.Report.TButton",
        )

        self.btn_configuracao.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=8,
        )

        # -----------------------------------------------------
        # BOTÃO DEMONSTRAÇÃO
        # -----------------------------------------------------

        self.btn_demonstracao = ttk.Button(
            self.reports_frame,
            text="DEMONSTRAÇÃO",
            command=self._clicar_demonstracao,
            style="PrinterView.Report.TButton",
        )

        self.btn_demonstracao.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=8,
        )

        # -----------------------------------------------------
        # DESCRIÇÃO
        # -----------------------------------------------------

        ttk.Label(
            self.reports_frame,
            text=(
                "Relatórios são enviados "
                "pelo serviço de impressão."
            ),
            style="PrinterView.Secondary.TLabel",
            justify="left",
            wraplength=180,
        ).grid(
            row=3,
            column=0,
            sticky="nw",
            pady=(
                12,
                0,
            ),
        )

        # -----------------------------------------------------
        # RODAPÉ
        # -----------------------------------------------------

        footer = tk.Frame(
            self,
            background=self.COR_FUNDO,
        )

        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=18,
            pady=(
                10,
                14,
            ),
        )

        footer.columnconfigure(
            0,
            weight=1,
        )

        # -----------------------------------------------------
        # FONTES
        # -----------------------------------------------------

        self.lbl_fontes = tk.Label(
            footer,
            text="",
            background=self.COR_FUNDO,
            foreground=self.COR_TEXTO_SECUNDARIO,
            font=(
                "Segoe UI",
                9,
            ),
            anchor="w",
        )

        self.lbl_fontes.grid(
            row=0,
            column=0,
            sticky="w",
        )

        # -----------------------------------------------------
        # BOTÕES
        # -----------------------------------------------------

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
            padx=(
                0,
                8,
            ),
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

    # =========================================================
    # CAMPO DE IDENTIFICAÇÃO
    # =========================================================

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

        if serial:

            label = self._texto_selecionavel(
                frame,
                "—",
                font=(
                    "Segoe UI",
                    11,
                    "bold",
                ),
                background=self.COR_PAINEL_2,
            )

        else:

            label = self._texto_selecionavel(
                frame,
                "—",
                font=(
                    "Segoe UI",
                    10,
                    "bold",
                ),
                background=self.COR_PAINEL_2,
            )

        label.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        # -----------------------------------------------------
        # NORMALIZAÇÃO DOS NOMES
        # -----------------------------------------------------

        nomes_atributos = {

            "Fabricante":
                "fabricante",

            "Modelo":
                "modelo",

            "Família":
                "familia",

            "Tipo":
                "tipo",

            "Serial":
                "serial",

            "Firmware":
                "firmware",

            "Contador":
                "contador",
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

    # =========================================================
    # NORMALIZAR TIPO DE CONSUMÍVEL
    # =========================================================

    @staticmethod
    def _tipo_consumivel(
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):

            return ""

        tipo = supply.get(
            "tipo"
        )

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

    # =========================================================
    # ATUALIZAÇÃO DA TELA
    # =========================================================

    def atualizar(
        self,
        device=None,
    ):

        if device is not None:

            self.device = device

        if self.device is None:

            return

        dados = self.device.to_dict()

        identificacao = dados.get(
            "identificacao",
            {},
        )

        conectividade = dados.get(
            "conectividade",
            {},
        )

        # -----------------------------------------------------
        # CABEÇALHO
        # -----------------------------------------------------

        modelo = identificacao.get(
            "modelo",
            "Impressora",
        )

        # O modelo vindo do sistema pode ser:
        #
        #     Lexmark MX611dhe
        #
        # portanto usamos exatamente o valor normalizado.
        self.lbl_modelo.config(
            text=modelo
        )

        self.lbl_ip.config(
            text=dados.get(
                "ip",
                "",
            )
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

        # -----------------------------------------------------
        # IDENTIFICAÇÃO
        # -----------------------------------------------------

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
                    .replace(
                        ",",
                        ".",
                    )
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

        # -----------------------------------------------------
        # CONSUMÍVEIS
        # -----------------------------------------------------

        self._atualizar_supplies(
            dados.get(
                "supplies",
                [],
            )
        )

        # -----------------------------------------------------
        # FONTES DE CONECTIVIDADE
        # -----------------------------------------------------

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
            text="    ".join(
                fontes
            )
        )

    # =========================================================
    # CONSUMÍVEIS
    # =========================================================

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
                text=(
                    "Nenhum consumível encontrado."
                ),
                background=self.COR_PAINEL,
                foreground=self.COR_TEXTO_SECUNDARIO,
                font=(
                    "Segoe UI",
                    10,
                ),
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
            scrollregion=(
                self.supplies_canvas.bbox(
                    "all"
                )
            )
        )

    # =========================================================
    # CARD DE CONSUMÍVEL
    # =========================================================

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

        # -----------------------------------------------------
        # IDENTIFICAÇÃO
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # NÍVEL
        # -----------------------------------------------------

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
            )
        )

        # -----------------------------------------------------
        # CABEÇALHO
        # -----------------------------------------------------

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

        titulo_widget = self._texto_selecionavel(
            card,
            titulo,
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
            background=self.COR_PAINEL_2,
        )

        titulo_widget.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=(
                8,
                0,
            ),
        )

        # -----------------------------------------------------
        # PORCENTAGEM
        # -----------------------------------------------------

        percentual = self._texto_selecionavel(
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

        percentual.grid(
            row=0,
            column=1,
            sticky="e",
            padx=10,
            pady=(
                8,
                0,
        ),
        )

        # -----------------------------------------------------
        # BARRA
        # -----------------------------------------------------

        barra = ttk.Progressbar(
            card,
            maximum=100,
            value=nivel,
            style="PrinterView.Horizontal.TProgressbar",
        )

        barra.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=10,
            pady=(
                5,
                7,
            ),
        )

        # -----------------------------------------------------
        # CAPACIDADE
        # -----------------------------------------------------

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

            detalhes_widget = self._texto_selecionavel(
                card,
                "   •   ".join(
                    detalhes
                ),
                font=(
                    "Segoe UI",
                    9,
                ),
                background=self.COR_PAINEL_2,
                foreground=self.COR_TEXTO_SECUNDARIO,
            )

            detalhes_widget.grid(
                row=2,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=10,
                pady=(
                    0,
                    3,
                ),
            )

        # -----------------------------------------------------
        # SERIAL
        # -----------------------------------------------------

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

                serial_widget = self._texto_selecionavel(
                    card,
                    f"Nº série: {serial}",
                    font=(
                        "Segoe UI",
                        9,
                        "bold",
                    ),
                    background=self.COR_PAINEL_2,
                )

                serial_widget.grid(
                    row=3,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    padx=10,
                    pady=(
                        2,
                        0,
                    ),
                )

        # -----------------------------------------------------
        # GARANTIA
        # -----------------------------------------------------

        if tipo == "unidade_imagem":

            garantia = supply.get(
                "garantia"
            )

            if garantia is True:

                texto = (
                    "Garantia: POSSÍVEL"
                )

                foreground = self.COR_ONLINE

            elif garantia is False:

                texto = (
                    "Garantia: NÃO ELEGÍVEL"
                )

                foreground = self.COR_OFFLINE

            else:

                texto = (
                    "Garantia: N/D"
                )

                foreground = self.COR_TEXTO_SECUNDARIO

            garantia_widget = self._texto_selecionavel(
                card,
                texto,
                font=(
                    "Segoe UI",
                    9,
                    "bold",
                ),
                background=self.COR_PAINEL_2,
                foreground=foreground,
            )

            garantia_widget.grid(
                row=4,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=10,
                pady=(
                    2,
                    8,
                ),
            )

        else:

            # -------------------------------------------------
            # ESPAÇO INFERIOR PARA CONSUMÍVEIS SEM GARANTIA
            # -------------------------------------------------

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

    # =========================================================
    # FORMATAÇÃO NUMÉRICA
    # =========================================================

    @staticmethod
    def _numero(
        valor,
    ):

        try:

            return (
                f"{int(valor):,}"
                .replace(
                    ",",
                    ".",
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return str(
                valor
            )

    # =========================================================
    # TEXTO DO TIPO
    # =========================================================

    @staticmethod
    def _texto_tipo(
        tipo,
    ):

        textos = {

            "toner":
                "Toner",

            "unidade_imagem":
                "Unidade de imagem",

            "fusor":
                "Fusor",
        }

        return textos.get(
            tipo,
            str(tipo),
        )

    # =========================================================
    # REPORT SERVICE
    # =========================================================

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

    # =========================================================
    # RELATÓRIO DE ATIVO
    # =========================================================

    def _clicar_relatorio_ativo(
        self,
    ):

        try:

            service = (
                self._criar_report_service()
            )

            resultado = (
                service.imprimir_ativo()
            )

            destino = resultado.get(
                "destino",
                "TSC",
            )

            messagebox.showinfo(
                "Printer Assistant",
                (
                    "Relatório de Ativo enviado "
                    "com sucesso.\n\n"
                    f"Destino: {destino}"
                ),
                parent=self,
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
                    "Ocorreu um erro ao imprimir "
                    "o Relatório de Ativo.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

    # =========================================================
    # CONFIGURAÇÃO E SUPRIMENTOS
    # =========================================================

    def _clicar_configuracao(
        self,
    ):

        try:

            service = (
                self._criar_report_service()
            )

            resultado = (
                service.imprimir_configuracao()
            )

            destino = resultado.get(
                "destino",
                "Impressora",
            )

            messagebox.showinfo(
                "Printer Assistant",
                (
                    "Relatório de Configuração "
                    "e Suprimentos enviado "
                    "com sucesso.\n\n"
                    f"Destino: {destino}"
                ),
                parent=self,
            )

        except ReportError as erro:

            messagebox.showerror(
                "Configuração e Suprimentos",
                str(erro),
                parent=self,
            )

        except Exception as erro:

            messagebox.showerror(
                "Configuração e Suprimentos",
                (
                    "Ocorreu um erro ao imprimir "
                    "o relatório.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

    # =========================================================
    # DEMONSTRAÇÃO
    # =========================================================

    def _clicar_demonstracao(
        self,
    ):

        try:

            service = (
                self._criar_report_service()
            )

            service.imprimir_demonstracao()

        except ReportError as erro:

            messagebox.showinfo(
                "Demonstração",
                str(erro),
                parent=self,
            )

        except Exception as erro:

            messagebox.showerror(
                "Demonstração",
                (
                    "Ocorreu um erro.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )

    # =========================================================
    # ATUALIZAR
    # =========================================================

    def _clicar_atualizar(
        self,
    ):

        if self.on_refresh:

            self.on_refresh()

        else:

            self.atualizar()

    # =========================================================
    # VOLTAR
    # =========================================================

    def _clicar_voltar(
        self,
    ):

        if self.on_back:

            self.on_back()