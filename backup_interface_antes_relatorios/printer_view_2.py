# PrinterView corrigido


import tkinter as tk
from tkinter import ttk


class PrinterView(ttk.Frame):
    """
    Ficha visual de uma impressora.

    Esta camada NÃO realiza comunicação com a impressora.

    Recebe um PrinterDevice e apresenta os dados retornados
    por device.to_dict().

    Regras desta etapa:

        - Não exibir Part Number.
        - Não processar Part Number.
        - Exibir serial da impressora.
        - Exibir serial do toner quando disponível.
        - Exibir serial da unidade de imagem quando disponível.
        - Fusor não possui campo de serial.
        - Garantia somente para unidade de imagem.
        - Origem do contador não é exibida.
        - Informações textuais são selecionáveis.
    """

    def __init__(
        self,
        master,
        device=None,
        on_refresh=None,
        on_back=None,
    ):

        super().__init__(
            master,
            padding=15,
        )

        self.device = device
        self.on_refresh = on_refresh
        self.on_back = on_back

        self.columnconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            2,
            weight=1,
        )

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

        self._cor_fundo = style.lookup(
            "TFrame",
            "background",
        )

        if not self._cor_fundo:
            self._cor_fundo = "#d9d9d9"

        style.configure(
            "Title.TLabel",
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
        )

        style.configure(
            "Subtitle.TLabel",
            font=(
                "Segoe UI",
                10,
            ),
        )

        style.configure(
            "Section.TLabel",
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
        )

        style.configure(
            "Value.TLabel",
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
        )

        style.configure(
            "Normal.TLabel",
            font=(
                "Segoe UI",
                10,
            ),
        )

        style.configure(
            "Serial.TLabel",
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
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
    ):

        if font is None:
            font = (
                "Segoe UI",
                10,
            )

        widget = tk.Text(
            parent,
            height=altura,
            width=largura if largura else 1,
            font=font,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            background=self._cor_fundo,
            foreground="#202020",
            insertbackground="#202020",
            selectbackground="#4a6984",
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
        # CABEÇALHO
        # -----------------------------------------------------

        header = ttk.Frame(
            self
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )

        header.columnconfigure(
            0,
            weight=1,
        )

        self.lbl_modelo = ttk.Label(
            header,
            text="Impressora",
            style="Title.TLabel",
        )

        self.lbl_modelo.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.lbl_ip = ttk.Label(
            header,
            text="",
            style="Subtitle.TLabel",
        )

        self.lbl_ip.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0),
        )

        self.lbl_estado = ttk.Label(
            header,
            text="",
            style="Value.TLabel",
            anchor="e",
        )

        self.lbl_estado.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
            padx=(15, 0),
        )

        # -----------------------------------------------------
        # IDENTIFICAÇÃO
        # -----------------------------------------------------

        identificacao = ttk.LabelFrame(
            self,
            text=" Identificação ",
            padding=10,
        )

        identificacao.grid(
            row=1,
            column=0,
            sticky="ew",
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

        # -----------------------------------------------------
        # ÁREA PRINCIPAL
        # -----------------------------------------------------

        principal = ttk.Frame(
            self
        )

        principal.grid(
            row=2,
            column=0,
            sticky="nsew",
        )

        principal.columnconfigure(
            0,
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
            text=" Consumíveis ",
            padding=10,
        )

        supplies_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
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
        # CANVAS + SCROLLBAR
        # -----------------------------------------------------

        canvas = tk.Canvas(
            supplies_frame,
            highlightthickness=0,
            borderwidth=0,
            background=self._cor_fundo,
        )

        scrollbar = ttk.Scrollbar(
            supplies_frame,
            orient="vertical",
            command=canvas.yview,
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

        self.supplies_container = ttk.Frame(
            canvas
        )

        self.supplies_window = canvas.create_window(
            (0, 0),
            window=self.supplies_container,
            anchor="nw",
        )

        # -----------------------------------------------------
        # ATUALIZAR ÁREA DE SCROLL
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # RODINHA DO MOUSE
        # -----------------------------------------------------

        def mousewheel(event):

            canvas.yview_scroll(
                int(
                    -1 * (event.delta / 120)
                ),
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

        # -----------------------------------------------------
        # RODAPÉ
        # -----------------------------------------------------

        footer = ttk.Frame(
            self
        )

        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        footer.columnconfigure(
            0,
            weight=1,
        )

        self.lbl_fontes = ttk.Label(
            footer,
            text="",
            style="Normal.TLabel",
        )

        self.lbl_fontes.grid(
            row=0,
            column=0,
            sticky="w",
        )

        botoes = ttk.Frame(
            footer
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
        )

        self.btn_voltar.pack(
            side="left",
            padx=(0, 8),
        )

        self.btn_atualizar = ttk.Button(
            botoes,
            text="Atualizar",
            command=self._clicar_atualizar,
        )

        self.btn_atualizar.pack(
            side="left",
        )

    # =========================================================
    # CAMPO
    # =========================================================

    def _campo(
        self,
        parent,
        titulo,
        row,
        column,
        serial=False,
    ):

        frame = ttk.Frame(
            parent
        )

        frame.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=4,
            pady=3,
        )

        ttk.Label(
            frame,
            text=titulo,
            style="Normal.TLabel",
        ).pack(
            anchor="w"
        )

        if serial:

            label = self._texto_selecionavel(
                frame,
                "—",
                font=(
                    "Segoe UI",
                    12,
                    "bold",
                ),
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
            )

        label.pack(
            fill="x",
            expand=True,
        )

        # Normaliza o nome do atributo.
        # Isso evita usar acentos em nomes internos do Python.
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
    # ATUALIZAÇÃO
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

        self.lbl_modelo.config(
            text=modelo
        )

        self.lbl_ip.config(
            text=dados.get(
                "ip",
                "",
            )
        )

        estado = dados.get(
            "estado",
            "OFFLINE",
        )

        self.lbl_estado.config(
            text=estado
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
        # FONTES
        # -----------------------------------------------------

        fontes = []

        for nome in (
            "pjl",
            "sysdebug",
            "snmp",
            "web",
            "raw",
            "ipp",
        ):

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

            ttk.Label(
                self.supplies_container,
                text="Nenhum consumível encontrado.",
                style="Normal.TLabel",
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

        card = ttk.LabelFrame(
            self.supplies_container,
            padding=10,
        )

        card.pack(
            fill="x",
            pady=5,
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
            ),
        )

        # -----------------------------------------------------
        # CABEÇALHO
        # -----------------------------------------------------

        titulo = str(
            nome
        )

        if tipo_texto and (
            tipo_texto.lower()
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
                12,
                "bold",
            ),
        )

        titulo_widget.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        # -----------------------------------------------------
        # PORCENTAGEM
        # -----------------------------------------------------

        percentual = self._texto_selecionavel(
            card,
            f"{nivel:.0f} %",
            font=(
                "Segoe UI",
                16,
                "bold",
            ),
            largura=7,
        )

        percentual.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(10, 0),
        )

        # -----------------------------------------------------
        # BARRA
        # -----------------------------------------------------

        barra = ttk.Progressbar(
            card,
            maximum=100,
            value=nivel,
        )

        barra.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(5, 7),
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
                f"Capacidade: {self._numero(capacidade)}"
            )

        if restante is not None:

            detalhes.append(
                f"Restante: {self._numero(restante)}"
            )

        if consumido is not None:

            detalhes.append(
                f"Consumido: {self._numero(consumido)}"
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
                "   •   ".join(detalhes),
                font=(
                    "Segoe UI",
                    10,
                ),
            )

            detalhes_widget.grid(
                row=2,
                column=0,
                columnspan=2,
                sticky="ew",
                pady=(0, 4),
            )

        # -----------------------------------------------------
        # SERIAL
        # -----------------------------------------------------

        if tipo != "fusor":

            serial = (
                supply.get("numero_serie")
                or supply.get("serial")
            )

            if serial:

                serial_widget = self._texto_selecionavel(
                    card,
                    f"Nº série: {serial}",
                    font=(
                        "Segoe UI",
                        11,
                        "bold",
                    ),
                )

                serial_widget.grid(
                    row=3,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    pady=(2, 0),
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

            elif garantia is False:

                texto = (
                    "Garantia: NÃO ELEGÍVEL"
                )

            else:

                texto = (
                    "Garantia: N/D"
                )

            garantia_widget = self._texto_selecionavel(
                card,
                texto,
                font=(
                    "Segoe UI",
                    10,
                    "bold",
                ),
            )

            garantia_widget.grid(
                row=4,
                column=0,
                columnspan=2,
                sticky="ew",
                pady=(2, 0),
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
    # ATUALIZAR
    # =========================================================

    def _clicar_atualizar(
        self
    ):

        if self.on_refresh:

            self.on_refresh()

        else:

            self.atualizar()

    # =========================================================
    # VOLTAR
    # =========================================================

    def _clicar_voltar(
        self
    ):

        if self.on_back:

            self.on_back()

