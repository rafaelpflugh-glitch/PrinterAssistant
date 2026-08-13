import tkinter as tk
from tkinter import ttk


class PrinterView(ttk.Frame):
    """
    Ficha visual de uma impressora.

    A interface NÃO coleta dados diretamente.
    Ela recebe um PrinterDevice e apresenta o resultado
    de device.to_dict().
    """

    def __init__(self, master, device=None, on_refresh=None):
        super().__init__(master, padding=20)

        self.device = device
        self.on_refresh = on_refresh

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

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

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 11),
        )

        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 12, "bold"),
        )

        style.configure(
            "Value.TLabel",
            font=("Segoe UI", 11, "bold"),
        )

        style.configure(
            "Normal.TLabel",
            font=("Segoe UI", 10),
        )

    # =========================================================
    # INTERFACE
    # =========================================================

    def _criar_interface(self):

        # -----------------------------------------------------
        # CABEÇALHO
        # -----------------------------------------------------

        header = ttk.Frame(self)
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 20),
        )

        header.columnconfigure(0, weight=1)

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
        )

        self.lbl_estado = ttk.Label(
            header,
            text="OFFLINE",
            style="Value.TLabel",
        )

        self.lbl_estado.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

        # -----------------------------------------------------
        # IDENTIFICAÇÃO
        # -----------------------------------------------------

        identificacao = ttk.LabelFrame(
            self,
            text=" Identificação ",
            padding=15,
        )

        identificacao.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 15),
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

        self._campo(
            identificacao,
            "Origem contador",
            1,
            3,
        )

        # -----------------------------------------------------
        # ÁREA PRINCIPAL
        # -----------------------------------------------------

        principal = ttk.Frame(self)

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
            padding=15,
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

        self.supplies_container = ttk.Frame(
            supplies_frame
        )

        self.supplies_container.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        # -----------------------------------------------------
        # RODAPÉ
        # -----------------------------------------------------

        footer = ttk.Frame(self)

        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(20, 0),
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

        self.btn_atualizar = ttk.Button(
            footer,
            text="Atualizar",
            command=self._clicar_atualizar,
        )

        self.btn_atualizar.grid(
            row=0,
            column=1,
            sticky="e",
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
    ):

        frame = ttk.Frame(parent)

        frame.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=5,
            pady=5,
        )

        ttk.Label(
            frame,
            text=titulo,
            style="Normal.TLabel",
        ).pack(
            anchor="w"
        )

        label = ttk.Label(
            frame,
            text="—",
            style="Value.TLabel",
        )

        label.pack(
            anchor="w"
        )

        atributo = (
            titulo.lower()
            .replace(" ", "_")
        )

        setattr(
            self,
            f"campo_{atributo}",
            label,
        )

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

        self.campo_fabricante.config(
            text=identificacao.get(
                "fabricante",
                "Desconhecido",
            )
        )

        self.campo_modelo.config(
            text=identificacao.get(
                "modelo",
                "Desconhecido",
            )
        )

        self.campo_família.config(
            text=identificacao.get(
                "familia",
                "",
            )
        )

        self.campo_tipo.config(
            text=identificacao.get(
                "tipo",
                "",
            )
        )

        self.campo_serial.config(
            text=identificacao.get(
                "serial",
                "Desconhecido",
            )
        )

        # Firmware pode estar no identificacao
        # ou diretamente no Device futuramente.
        firmware = identificacao.get(
            "firmware",
            dados.get(
                "firmware",
                "Desconhecido",
            ),
        )

        self.campo_firmware.config(
            text=firmware
        )

        contador = identificacao.get(
            "contador"
        )

        if contador is None:
            contador_texto = "Desconhecido"
        else:
            contador_texto = (
                f"{contador:,}"
                .replace(",", ".")
            )

        self.campo_contador.config(
            text=contador_texto
        )

        self.campo_origem_contador.config(
            text=dados.get(
                "origem_contador",
                "Desconhecida",
            )
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

            simbolo = "●" if ativo else "○"

            fontes.append(
                f"{nome.upper()} {simbolo}"
            )

        self.lbl_fontes.config(
            text="    ".join(fontes)
        )

    # =========================================================
    # SUPPLIES
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

    # =========================================================
    # CARD DE SUPPLY
    # =========================================================

    def _criar_supply_card(
        self,
        numero,
        supply,
    ):

        card = ttk.Frame(
            self.supplies_container,
            padding=10,
            relief="groove",
        )

        card.pack(
            fill="x",
            pady=5,
        )

        card.columnconfigure(
            0,
            weight=1,
        )

        nome = supply.get(
            "nome",
            f"Consumível {numero}",
        )

        tipo = supply.get(
            "tipo",
            "",
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
            nivel = float(nivel)
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

        ttk.Label(
            card,
            text=nome,
            style="Section.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            card,
            text=f"{nivel:.0f}%",
            style="Value.TLabel",
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

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
            pady=5,
        )

        restante = supply.get(
            "restante"
        )

        condicao = supply.get(
            "condicao",
            "N/D",
        )

        serial = (
            supply.get(
                "numero_serie"
            )
            or
            "N/D"
        )

        detalhes = []

        if tipo:
            detalhes.append(
                str(tipo)
            )

        if restante is not None:
            try:
                restante_texto = (
                    f"{int(restante):,}"
                    .replace(",", ".")
                )
            except (
                TypeError,
                ValueError,
            ):
                restante_texto = str(
                    restante
                )

            detalhes.append(
                f"{restante_texto} restantes"
            )

        detalhes.append(
            str(condicao)
        )

        ttk.Label(
            card,
            text=" • ".join(
                detalhes
            ),
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
        )

        ttk.Label(
            card,
            text=f"Nº série: {serial}",
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
        )

        garantia = supply.get(
            "garantia"
        )

        if tipo == "unidade_imagem":

            if garantia is True:
                texto = "Garantia: POSSÍVEL"

            elif garantia is False:
                texto = "Garantia: NÃO ELEGÍVEL"

            else:
                texto = "Garantia: N/D"

            ttk.Label(
                card,
                text=texto,
            ).grid(
                row=4,
                column=0,
                columnspan=2,
                sticky="w",
            )

    # =========================================================
    # ATUALIZAR
    # =========================================================

    def _clicar_atualizar(self):

        if self.on_refresh:
            self.on_refresh()
        else:
            self.atualizar()