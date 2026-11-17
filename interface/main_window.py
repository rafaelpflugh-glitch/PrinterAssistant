import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from core.device import PrinterDevice
from core.scanner import (
    descobrir_candidatos,
    identificar,
)
from interface.printer_view import PrinterView
from interface.settings_window import SettingsWindow
from interface.theme import aplicar_tema
from core.version import __version__, APP_TITLE


class MainWindow(tk.Tk):

    """
    Janela principal do Printer Assistant.

    Fluxo operacional:

        1. Descobrir rede local
        2. Descobrir equipamentos
        3. Identificar candidatos
        4. Técnico seleciona a impressora (ou adiciona IP manualmente)
        5. Coletar PJL + SYSDEBUG + SNMP
        6. Exibir ficha da impressora
    """

    def __init__(
        self,
    ):

        super().__init__()

        # -----------------------------------------------------
        # TEMA GLOBAL
        # -----------------------------------------------------

        aplicar_tema(self)

        self.title(
            APP_TITLE
        )

        self.geometry(
            "1100x780"
        )

        self.minsize(
            900,
            650,
        )

        self.device = None

        self.resultados_descoberta = []

        self.ip_local = None
        self.rede_local = None

        self.printer_view = None

        self._coleta_em_andamento = False

        self._criar_interface()

        self.after(
            300,
            self.iniciar_descoberta,
        )


    # =========================================================
    # INTERFACE
    # =========================================================

    def _criar_interface(
        self,
    ):

        # -----------------------------------------------------
        # TOPO
        # -----------------------------------------------------

        topo = ttk.Frame(
            self,
            padding=(20, 15),
        )

        topo.pack(
            fill="x"
        )

        topo.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            topo,
            text=f"Printer Assistant  {__version__}",
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.lbl_rede = ttk.Label(
            topo,
            text="Rede: identificando...",
        )

        self.lbl_rede.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 0),
        )

        botoes_topo = ttk.Frame(
            topo,
        )

        botoes_topo.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

        self.btn_config = ttk.Button(
            botoes_topo,
            text="⚙ Configurações",
            command=self.abrir_configuracoes,
        )

        self.btn_config.pack(
            side="left",
            padx=(0, 6),
        )

        self.btn_manual = ttk.Button(
            botoes_topo,
            text="Adicionar IP Manual",
            command=self.adicionar_ip_manual,
        )

        self.btn_manual.pack(
            side="left",
            padx=(0, 6),
        )

        self.btn_redescobrir = ttk.Button(
            botoes_topo,
            text="Redescobrir",
            command=self.iniciar_descoberta,
        )

        self.btn_redescobrir.pack(
            side="left",
        )


        # -----------------------------------------------------
        # STATUS
        # -----------------------------------------------------

        status_frame = ttk.Frame(
            self,
            padding=(20, 0, 20, 10),
        )

        status_frame.pack(
            fill="x"
        )

        self.lbl_status = ttk.Label(
            status_frame,
            text="Inicializando...",
        )

        self.lbl_status.pack(
            side="left"
        )


        # -----------------------------------------------------
        # ÁREA PRINCIPAL
        # -----------------------------------------------------

        self.area = ttk.Frame(
            self,
            padding=(20, 0, 20, 20),
        )

        self.area.pack(
            fill="both",
            expand=True,
        )

        self.area.columnconfigure(
            0,
            weight=1,
        )

        self.area.rowconfigure(
            0,
            weight=1,
        )

        self._mostrar_tela_descoberta()


    # =========================================================
    # CONFIGURAÇÕES
    # =========================================================

    def abrir_configuracoes(
        self,
    ):

        SettingsWindow(
            self
        )


    # =========================================================
    # ADICIONAR IP MANUAL
    # =========================================================

    def adicionar_ip_manual(
        self,
    ):

        ip_digitado = simpledialog.askstring(
            "Adicionar IP Manual",
            "Digite o endereço IP da impressora (ex: 192.168.14.152):",
            parent=self,
        )

        if not ip_digitado:
            return

        ip_limpo = ip_digitado.strip()

        partes = ip_limpo.split(".")

        if len(partes) != 4:
            messagebox.showerror(
                "Erro",
                "Formato de IP inválido.",
                parent=self,
            )
            return

        self.lbl_status.config(
            text=f"Testando IP manual {ip_limpo}..."
        )

        self.btn_redescobrir.config(
            state="disabled"
        )

        self.btn_manual.config(
            state="disabled"
        )

        threading.Thread(
            target=self._identificar_ip_manual_thread,
            args=(ip_limpo,),
            daemon=True,
        ).start()


    def _identificar_ip_manual_thread(
        self,
        ip,
    ):

        try:
            resultado = asyncio.run(identificar(ip))
            self.after(
                0,
                lambda: self._ip_manual_concluido(resultado),
            )
        except Exception as e:
            self.after(
                0,
                lambda: self._ip_manual_erro(str(e)),
            )


    def _ip_manual_concluido(
        self,
        resultado,
    ):

        self.btn_redescobrir.config(
            state="normal"
        )

        self.btn_manual.config(
            state="normal"
        )

        if not resultado or not resultado.get("device"):
            messagebox.showerror(
                "Erro",
                "Não foi possível identificar o equipamento neste IP.",
                parent=self,
            )
            self.lbl_status.config(
                text="Falha na identificação manual."
            )
            return

        self.resultados_descoberta.append(resultado)

        novo_indice = len(self.resultados_descoberta) - 1

        device = resultado["device"]

        identificacao = device.identificacao

        modelo = identificacao.get("modelo", "Desconhecido")
        fabricante = identificacao.get("fabricante", "Desconhecido")
        serial = identificacao.get("serial", "Desconhecido")
        contador = identificacao.get("contador")

        if contador is None:
            contador_texto = "Desconhecido"
        else:
            try:
                contador_texto = f"{int(contador):,}".replace(",", ".")
            except (TypeError, ValueError):
                contador_texto = str(contador)

        self.tree.insert(
            "",
            "end",
            iid=str(novo_indice),
            values=(
                modelo,
                fabricante,
                serial,
                contador_texto,
                device.estado(),
            ),
        )

        self.lbl_status.config(
            text=f"Equipamento {device.ip} adicionado com sucesso!"
        )

        messagebox.showinfo(
            "Sucesso",
            f"Impressora {modelo} ({device.ip}) adicionada à lista!",
            parent=self,
        )


    def _ip_manual_erro(
        self,
        erro,
    ):

        self.btn_redescobrir.config(
            state="normal"
        )

        self.btn_manual.config(
            state="normal"
        )

        self.lbl_status.config(
            text="Erro ao testar IP manual."
        )

        messagebox.showerror(
            "Erro",
            f"Erro de conexão com o IP:\n{erro}",
            parent=self,
        )


    # =========================================================
    # TELA DE DESCOBERTA
    # =========================================================

    def _mostrar_tela_descoberta(
        self,
    ):

        for widget in (
            self.area.winfo_children()
        ):

            widget.destroy()

        frame = ttk.Frame(
            self.area,
            padding=30,
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

        frame.rowconfigure(
            2,
            weight=1,
        )


        ttk.Label(
            frame,
            text="Impressoras encontradas",
            font=(
                "Segoe UI",
                17,
                "bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5),
        )


        ttk.Label(
            frame,
            text=(
                "Selecione a impressora que deseja diagnosticar ou adicione um IP manualmente."
            ),
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 15),
        )


        tabela_frame = ttk.Frame(
            frame
        )

        tabela_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
        )

        tabela_frame.columnconfigure(
            0,
            weight=1,
        )

        tabela_frame.rowconfigure(
            0,
            weight=1,
        )


        colunas = (
            "modelo",
            "fabricante",
            "serial",
            "contador",
            "estado",
        )


        self.tree = ttk.Treeview(
            tabela_frame,
            columns=colunas,
            show="headings",
            selectmode="browse",
        )


        self.tree.heading(
            "modelo",
            text="Impressora",
        )

        self.tree.heading(
            "fabricante",
            text="Fabricante",
        )

        self.tree.heading(
            "serial",
            text="Serial",
        )

        self.tree.heading(
            "contador",
            text="Contador",
        )

        self.tree.heading(
            "estado",
            text="Estado",
        )


        self.tree.column(
            "modelo",
            width=260,
            anchor="w",
        )

        self.tree.column(
            "fabricante",
            width=130,
            anchor="w",
        )

        self.tree.column(
            "serial",
            width=180,
            anchor="w",
        )

        self.tree.column(
            "contador",
            width=120,
            anchor="e",
        )

        self.tree.column(
            "estado",
            width=120,
            anchor="center",
        )


        scrollbar = ttk.Scrollbar(
            tabela_frame,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )


        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )


        self.tree.bind(
            "<Double-1>",
            lambda evento:
            self.selecionar_impressora(),
        )


        botoes = ttk.Frame(
            frame
        )

        botoes.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(15, 0),
        )

        botoes.columnconfigure(
            0,
            weight=1,
        )


        self.btn_selecionar = ttk.Button(
            botoes,
            text="Selecionar impressora",
            command=self.selecionar_impressora,
        )

        self.btn_selecionar.grid(
            row=0,
            column=1,
        )


    # =========================================================
    # INICIAR DESCOBERTA
    # =========================================================

    def iniciar_descoberta(
        self,
    ):

        if self._coleta_em_andamento:

            return

        self.btn_redescobrir.config(
            state="disabled"
        )

        self.lbl_status.config(
            text="Descobrindo rede local..."
        )

        self.lbl_rede.config(
            text="Rede: identificando..."
        )

        self._mostrar_tela_descoberta()

        thread = threading.Thread(
            target=self._descoberta_thread,
            daemon=True,
        )

        thread.start()


    # =========================================================
    # THREAD DESCOBERTA
    # =========================================================

    def _descoberta_thread(
        self,
    ):

        try:

            resultado = asyncio.run(
                self._executar_descoberta()
            )

            self.after(
                0,
                lambda:
                self._descoberta_concluida(
                    resultado
                ),
            )

        except Exception as erro:

            self.after(
                0,
                lambda:
                self._descoberta_erro(
                    erro
                ),
            )


    # =========================================================
    # EXECUTAR DESCOBERTA
    # =========================================================

    async def _executar_descoberta(
        self,
    ):

        (
            ip_local,
            rede,
            candidatos,
        ) = await descobrir_candidatos()

        if not candidatos:

            return (
                ip_local,
                rede,
                [],
            )


        tarefas = [
            identificar(ip)
            for ip in candidatos
        ]

        identificados = await asyncio.gather(
            *tarefas,
            return_exceptions=True,
        )


        resultados = []

        for item in identificados:

            if isinstance(
                item,
                Exception,
            ):

                continue

            if not isinstance(
                item,
                dict,
            ):

                continue

            device = item.get(
                "device"
            )

            if device is None:

                continue

            resultados.append(
                item
            )


        resultados.sort(
            key=lambda item: (

                item["device"].modelo()
                == "Desconhecido",

                item["device"].serial()
                == "Desconhecido",
            )
        )


        return (
            ip_local,
            rede,
            resultados,
        )


    # =========================================================
    # DESCOBERTA CONCLUÍDA
    # =========================================================

    def _descoberta_concluida(
        self,
        resultado,
    ):

        (
            self.ip_local,
            self.rede_local,
            resultados,
        ) = resultado

        self.resultados_descoberta = (
            resultados
        )


        self.lbl_rede.config(
            text=(
                f"Rede: {self.rede_local}   "
                f"| Computador: {self.ip_local}"
            )
        )


        self.btn_redescobrir.config(
            state="normal"
        )


        if not resultados:

            self.lbl_status.config(
                text=(
                    "Nenhuma impressora encontrada."
                )
            )

            self._mostrar_tela_descoberta()

            return


        self.lbl_status.config(
            text=(
                f"{len(resultados)} "
                "equipamento(s) encontrado(s)."
            )
        )


        self._mostrar_tela_descoberta()


        for indice, item in enumerate(
            resultados
        ):

            device = item.get(
                "device"
            )

            if device is None:

                continue

            identificacao = (
                device.identificacao
            )


            modelo = identificacao.get(
                "modelo",
                "Desconhecido",
            )

            fabricante = identificacao.get(
                "fabricante",
                "Desconhecido",
            )

            serial = identificacao.get(
                "serial",
                "Desconhecido",
            )

            contador = identificacao.get(
                "contador"
            )


            if contador is None:

                contador_texto = (
                    "Desconhecido"
                )

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


            self.tree.insert(
                "",
                "end",
                iid=str(
                    indice
                ),
                values=(
                    modelo,
                    fabricante,
                    serial,
                    contador_texto,
                    device.estado(),
                ),
            )


    # =========================================================
    # ERRO DESCOBERTA
    # =========================================================

    def _descoberta_erro(
        self,
        erro,
    ):

        self.btn_redescobrir.config(
            state="normal"
        )

        self.lbl_status.config(
            text="Erro durante a descoberta."
        )

        messagebox.showerror(
            "Printer Assistant",
            (
                "Não foi possível descobrir "
                "as impressoras da rede.\n\n"
                f"{erro}"
            ),
        )


    # =========================================================
    # SELECIONAR IMPRESSORA
    # =========================================================

    def selecionar_impressora(
        self,
    ):

        if self._coleta_em_andamento:

            return

        selecao = self.tree.selection()


        if not selecao:

            messagebox.showwarning(
                "Printer Assistant",
                "Selecione uma impressora.",
            )

            return


        try:

            indice = int(
                selecao[0]
            )

            item = (
                self.resultados_descoberta[
                    indice
                ]
            )

        except (
            ValueError,
            IndexError,
        ):

            messagebox.showerror(
                "Printer Assistant",
                (
                    "Não foi possível identificar "
                    "a impressora selecionada."
                ),
            )

            return


        device = item.get(
            "device"
        )


        if device is None:

            messagebox.showerror(
                "Printer Assistant",
                "Equipamento inválido.",
            )

            return


        self.device = device

        self._coleta_em_andamento = True

        self.btn_redescobrir.config(
            state="disabled"
        )

        self.btn_selecionar.config(
            state="disabled"
        )

        self.lbl_status.config(
            text=(
                "Coletando dados completos..."
            )
        )


        thread = threading.Thread(
            target=self._coleta_completa_thread,
            args=(
                device.ip,
            ),
            daemon=True,
        )

        thread.start()


    # =========================================================
    # COLETA COMPLETA
    # =========================================================

    def _coleta_completa_thread(
        self,
        ip,
    ):

        try:

            device = PrinterDevice(
                ip=ip
            )

            asyncio.run(
                device.coletar()
            )


            self.after(
                0,
                lambda:
                self._coleta_concluida(
                    device
                ),
            )


        except Exception as erro:

            self.after(
                0,
                lambda:
                self._coleta_erro(
                    erro
                ),
            )


    # =========================================================
    # COLETA CONCLUÍDA
    # =========================================================

    def _coleta_concluida(
        self,
        device,
    ):

        self.device = device

        self._coleta_em_andamento = False


        for widget in (
            self.area.winfo_children()
        ):

            widget.destroy()


        self.printer_view = PrinterView(
            self.area,
            device=device,
            on_refresh=self.atualizar,
            on_back=self.voltar_para_descoberta,
        )


        self.printer_view.grid(
            row=0,
            column=0,
            sticky="nsew",
        )


        self.lbl_status.config(
            text="Coleta concluída."
        )


        self.btn_redescobrir.config(
            state="normal"
        )


    # =========================================================
    # ERRO COLETA
    # =========================================================

    def _coleta_erro(
        self,
        erro,
    ):

        self._coleta_em_andamento = False

        self.btn_redescobrir.config(
            state="normal"
        )

        self.lbl_status.config(
            text="Erro durante a coleta."
        )

        messagebox.showerror(
            "Printer Assistant",
            (
                "Não foi possível concluir "
                "a coleta da impressora.\n\n"
                f"{erro}"
            ),
        )


    # =========================================================
    # ATUALIZAR
    # =========================================================

    def atualizar(
        self,
    ):

        if self.device is None:

            return

        if self._coleta_em_andamento:

            return

        self._coleta_em_andamento = True

        self.btn_redescobrir.config(
            state="disabled"
        )

        self.lbl_status.config(
            text="Atualizando impressora..."
        )


        ip = self.device.ip


        thread = threading.Thread(
            target=self._coleta_completa_thread,
            args=(
                ip,
            ),
            daemon=True,
        )

        thread.start()


    # =========================================================
    # VOLTAR
    # =========================================================

    def voltar_para_descoberta(
        self,
    ):

        self.device = None

        self.printer_view = None

        self._coleta_em_andamento = False

        self.btn_redescobrir.config(
            state="normal"
        )

        self.lbl_status.config(
            text="Selecione uma impressora."
        )

        self._mostrar_tela_descoberta()


        # -----------------------------------------------------
        # RECARREGAR LISTA
        # -----------------------------------------------------

        for indice, item in enumerate(
            self.resultados_descoberta
        ):

            device = item.get(
                "device"
            )

            if device is None:

                continue


            identificacao = (
                device.identificacao
            )


            modelo = identificacao.get(
                "modelo",
                "Desconhecido",
            )

            fabricante = identificacao.get(
                "fabricante",
                "Desconhecido",
            )

            serial = identificacao.get(
                "serial",
                "Desconhecido",
            )

            contador = identificacao.get(
                "contador"
            )


            if contador is None:

                contador_texto = (
                    "Desconhecido"
                )

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


            self.tree.insert(
                "",
                "end",
                iid=str(
                    indice
                ),
                values=(
                    modelo,
                    fabricante,
                    serial,
                    contador_texto,
                    device.estado(),
                ),
            )


# =============================================================
# INICIAR
# =============================================================

def iniciar():

    app = MainWindow()

    app.mainloop()