import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from core.device import PrinterDevice
from interface.printer_view import PrinterView


class MainWindow(tk.Tk):
    """
    Janela principal do Printer Assistant.

    Nesta primeira versão usamos um IP manual apenas
    para validar a integração com o PrinterDevice.

    O Discovery será integrado depois.
    """

    def __init__(self):

        super().__init__()

        self.title(
            "Printer Assistant"
        )

        self.geometry(
            "1050x760"
        )

        self.minsize(
            850,
            600,
        )

        self.device = None

        self._criar_interface()

    # =========================================================
    # INTERFACE
    # =========================================================

    def _criar_interface(self):

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

        ttk.Label(
            topo,
            text="Printer Assistant",
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
        ).pack(
            side="left"
        )

        # -----------------------------------------------------
        # CONTROLE DE IP
        # -----------------------------------------------------

        controles = ttk.Frame(
            self,
            padding=(20, 0, 20, 10),
        )

        controles.pack(
            fill="x"
        )

        ttk.Label(
            controles,
            text="IP da impressora:",
        ).pack(
            side="left"
        )

        self.entry_ip = ttk.Entry(
            controles,
            width=22,
        )

        self.entry_ip.pack(
            side="left",
            padx=8,
        )

        # IP atual usado somente para laboratório.
        self.entry_ip.insert(
            0,
            "192.168.14.134",
        )

        self.btn_conectar = ttk.Button(
            controles,
            text="Conectar",
            command=self.conectar,
        )

        self.btn_conectar.pack(
            side="left",
        )

        self.lbl_status = ttk.Label(
            controles,
            text="Aguardando...",
        )

        self.lbl_status.pack(
            side="left",
            padx=15,
        )

        # -----------------------------------------------------
        # ÁREA DA IMPRESSORA
        # -----------------------------------------------------

        self.area = ttk.Frame(
            self,
            padding=(20, 0, 20, 20),
        )

        self.area.pack(
            fill="both",
            expand=True,
        )

        # -----------------------------------------------------
        # MENSAGEM INICIAL
        # -----------------------------------------------------

        self.lbl_inicio = ttk.Label(
            self.area,
            text=(
                "Digite o IP da impressora "
                "e clique em Conectar."
            ),
            font=(
                "Segoe UI",
                13,
            ),
        )

        self.lbl_inicio.pack(
            expand=True
        )

    # =========================================================
    # CONECTAR
    # =========================================================

    def conectar(self):

        ip = (
            self.entry_ip.get()
            .strip()
        )

        if not ip:

            messagebox.showwarning(
                "Printer Assistant",
                "Informe o IP da impressora.",
            )

            return

        self.btn_conectar.config(
            state="disabled"
        )

        self.lbl_status.config(
            text="Coletando..."
        )

        thread = threading.Thread(
            target=self._coletar_thread,
            args=(ip,),
            daemon=True,
        )

        thread.start()

    # =========================================================
    # THREAD DE COLETA
    # =========================================================

    def _coletar_thread(
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
                lambda: self._coleta_concluida(
                    device
                ),
            )

        except Exception as erro:

            self.after(
                0,
                lambda: self._coleta_erro(
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

        self.lbl_inicio.pack_forget()

        # Remove visualização anterior.
        for widget in (
            self.area.winfo_children()
        ):
            widget.destroy()

        self.printer_view = PrinterView(
            self.area,
            device=device,
            on_refresh=self.atualizar,
        )

        self.printer_view.pack(
            fill="both",
            expand=True,
        )

        self.lbl_status.config(
            text="Coleta concluída"
        )

        self.btn_conectar.config(
            state="normal"
        )

    # =========================================================
    # ERRO
    # =========================================================

    def _coleta_erro(
        self,
        erro,
    ):

        self.lbl_status.config(
            text="Erro"
        )

        self.btn_conectar.config(
            state="normal"
        )

        messagebox.showerror(
            "Erro",
            str(erro),
        )

    # =========================================================
    # ATUALIZAR
    # =========================================================

    def atualizar(self):

        if self.device is None:
            return

        self.btn_conectar.config(
            state="disabled"
        )

        self.lbl_status.config(
            text="Atualizando..."
        )

        ip = self.device.ip

        thread = threading.Thread(
            target=self._coletar_thread,
            args=(ip,),
            daemon=True,
        )

        thread.start()


def iniciar():

    app = MainWindow()

    app.mainloop()