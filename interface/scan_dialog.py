"""
Janela de visualização, impressão e digitalização do relatório.

Fluxo:

    PrinterDevice já coletado
            ↓
    montar relatório
            ↓
    visualizar relatório
            ↓
    imprimir relatório
            ↓
    digitalizar relatório
            ↓
    visualizar / armazenar digitalização

IMPORTANTE:

    Esta janela NÃO realiza nova coleta da impressora.

    O PrinterDevice recebido deve estar previamente coletado.

    A comunicação real com o scanner ainda será realizada
    posteriormente através do ScanService.

    NÃO colocar subprocess, CGI, socket ou comunicação direta
    com scanner nesta interface.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox


# ============================================================
# RELATÓRIO
# ============================================================

from core.relatorio_suprimentos import (
    extrair_dados,
    montar_texto,
    gerar_pcl,
    imprimir,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PORTA_RAW = 9100


# ============================================================
# JANELA
# ============================================================

class ScanDialog(tk.Toplevel):

    def __init__(
        self,
        parent,
        device=None,
    ):

        super().__init__(parent)

        self.device = device

        self.texto_relatorio = ""

        self.dados_pcl = None

        self.ip = ""

        self._impressao_em_andamento = False

        self._criar_janela()

        self._criar_interface()

        self._preparar_relatorio()


    # ========================================================
    # JANELA
    # ========================================================

    def _criar_janela(self):

        self.title(
            "Relatório de configuração"
        )

        self.geometry(
            "850x700"
        )

        self.minsize(
            700,
            550,
        )

        self.resizable(
            True,
            True,
        )

        self.transient(
            self.master
        )

        self.grab_set()


    # ========================================================
    # INTERFACE
    # ========================================================

    def _criar_interface(self):

        container = ttk.Frame(
            self,
            padding=20,
        )

        container.pack(
            fill="both",
            expand=True,
        )

        container.columnconfigure(
            0,
            weight=1,
        )

        container.rowconfigure(
            2,
            weight=1,
        )


        # ----------------------------------------------------
        # CABEÇALHO
        # ----------------------------------------------------

        ttk.Label(
            container,
            text="RELATÓRIO DE CONFIGURAÇÃO E SUPRIMENTOS",
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


        self.lbl_impressora = ttk.Label(
            container,
            text="Impressora: carregando...",
        )

        self.lbl_impressora.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 12),
        )


        # ----------------------------------------------------
        # ÁREA DO RELATÓRIO
        # ----------------------------------------------------

        relatorio_frame = ttk.Frame(
            container
        )

        relatorio_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
        )

        relatorio_frame.columnconfigure(
            0,
            weight=1,
        )

        relatorio_frame.rowconfigure(
            0,
            weight=1,
        )


        self.txt_relatorio = tk.Text(
            relatorio_frame,

            wrap="none",

            font=(
                "Consolas",
                10,
            ),

            padx=12,
            pady=12,

            state="disabled",
        )


        scrollbar_vertical = ttk.Scrollbar(
            relatorio_frame,
            orient="vertical",
            command=self.txt_relatorio.yview,
        )

        scrollbar_horizontal = ttk.Scrollbar(
            relatorio_frame,
            orient="horizontal",
            command=self.txt_relatorio.xview,
        )


        self.txt_relatorio.configure(
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set,
        )


        self.txt_relatorio.grid(
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


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.lbl_status = ttk.Label(
            container,
            text="Preparando relatório...",
        )

        self.lbl_status.grid(
            row=3,
            column=0,
            sticky="w",
            pady=(12, 10),
        )


        # ----------------------------------------------------
        # BOTÕES
        # ----------------------------------------------------

        botoes = ttk.Frame(
            container
        )

        botoes.grid(
            row=4,
            column=0,
            sticky="ew",
        )

        botoes.columnconfigure(
            0,
            weight=1,
        )


        self.btn_cancelar = ttk.Button(
            botoes,
            text="AGORA NÃO",
            command=self.destroy,
        )

        self.btn_cancelar.grid(
            row=0,
            column=0,
            sticky="w",
        )


        self.btn_imprimir = ttk.Button(
            botoes,
            text="IMPRIMIR RELATÓRIO",
            command=self._imprimir_relatorio,
        )

        self.btn_imprimir.grid(
            row=0,
            column=1,
            sticky="e",
        )


    # ========================================================
    # PREPARAR RELATÓRIO
    # ========================================================

    def _preparar_relatorio(self):

        if self.device is None:

            self.lbl_status.config(
                text="Nenhuma impressora foi fornecida."
            )

            self.btn_imprimir.config(
                state="disabled"
            )

            messagebox.showerror(
                "Printer Assistant",
                (
                    "Não foi possível preparar o relatório.\n\n"
                    "Nenhuma impressora foi fornecida."
                ),
                parent=self,
            )

            return


        try:

            (
                identificacao,
                supplies,
                ip,
            ) = extrair_dados(
                self.device
            )


            self.ip = ip


            self.texto_relatorio = montar_texto(
                identificacao,
                supplies,
                ip,
            )


            self.dados_pcl = gerar_pcl(
                self.texto_relatorio
            )


            modelo = identificacao.get(
                "modelo",
                "Desconhecido",
            )

            serial = identificacao.get(
                "serial",
                "Desconhecido",
            )


            self.lbl_impressora.config(
                text=(
                    f"Impressora: {modelo}   "
                    f"| Serial: {serial}   "
                    f"| IP: {ip or 'N/D'}"
                )
            )


            self._mostrar_relatorio()


            self.lbl_status.config(
                text=(
                    "Relatório preparado. "
                    "Confira os dados antes de imprimir."
                )
            )


        except Exception as erro:

            self.lbl_status.config(
                text="Erro ao preparar relatório."
            )

            self.btn_imprimir.config(
                state="disabled"
            )

            messagebox.showerror(
                "Printer Assistant",
                (
                    "Não foi possível preparar "
                    "o relatório.\n\n"
                    f"{erro}"
                ),
                parent=self,
            )


    # ========================================================
    # MOSTRAR RELATÓRIO
    # ========================================================

    def _mostrar_relatorio(self):

        self.txt_relatorio.config(
            state="normal"
        )

        self.txt_relatorio.delete(
            "1.0",
            "end",
        )

        self.txt_relatorio.insert(
            "1.0",
            self.texto_relatorio,
        )

        self.txt_relatorio.config(
            state="disabled"
        )

        self.txt_relatorio.yview_moveto(
            0
        )

        self.txt_relatorio.xview_moveto(
            0
        )


    # ========================================================
    # IMPRIMIR
    # ========================================================

    def _imprimir_relatorio(self):

        if self._impressao_em_andamento:

            return


        if not self.dados_pcl:

            messagebox.showerror(
                "Printer Assistant",
                (
                    "O relatório PCL não está disponível."
                ),
                parent=self,
            )

            return


        if not self.ip:

            messagebox.showerror(
                "Printer Assistant",
                (
                    "O endereço IP da impressora "
                    "não está disponível."
                ),
                parent=self,
            )

            return


        confirmar = messagebox.askyesno(
            "Imprimir relatório",
            (
                "O relatório será enviado para a impressora.\n\n"
                "Deseja continuar?"
            ),
            parent=self,
        )


        if not confirmar:

            return


        self._impressao_em_andamento = True


        self.btn_imprimir.config(
            state="disabled"
        )

        self.btn_cancelar.config(
            state="disabled"
        )


        self.lbl_status.config(
            text=(
                "Enviando relatório para a impressora..."
            )
        )


        thread = threading.Thread(
            target=self._impressao_thread,
            daemon=True,
        )

        thread.start()


    # ========================================================
    # THREAD DE IMPRESSÃO
    # ========================================================

    def _impressao_thread(self):

        try:

            imprimir(
                self.dados_pcl,
                self.ip,
                PORTA_RAW,
            )


            self.after(
                0,
                self._impressao_concluida,
            )


        except Exception as erro:

            self.after(
                0,
                lambda:
                self._impressao_erro(
                    erro
                ),
            )


    # ========================================================
    # IMPRESSÃO CONCLUÍDA
    # ========================================================

    def _impressao_concluida(self):

        self._impressao_em_andamento = False


        self.btn_cancelar.config(
            state="normal"
        )


        self.lbl_status.config(
            text=(
                "Relatório impresso com sucesso."
            )
        )


        messagebox.showinfo(
            "Printer Assistant",
            (
                "O relatório foi enviado "
                "para a impressora com sucesso."
            ),
            parent=self,
        )


        self._mostrar_etapa_digitalizacao()


    # ========================================================
    # ERRO DE IMPRESSÃO
    # ========================================================

    def _impressao_erro(
        self,
        erro,
    ):

        self._impressao_em_andamento = False


        self.btn_imprimir.config(
            state="normal"
        )

        self.btn_cancelar.config(
            state="normal"
        )


        self.lbl_status.config(
            text="Erro durante a impressão."
        )


        messagebox.showerror(
            "Printer Assistant",
            (
                "Não foi possível imprimir "
                "o relatório.\n\n"
                f"{erro}"
            ),
            parent=self,
        )


    # ========================================================
    # ETAPA DE DIGITALIZAÇÃO
    # ========================================================

    def _mostrar_etapa_digitalizacao(self):

        """
        Prepara a interface para a próxima etapa.

        A comunicação real com o scanner ainda NÃO é realizada.

        Quando o ScanService estiver implementado,
        esta função será o ponto de entrada para ele.
        """

        self.btn_imprimir.config(
            state="disabled"
        )


        self.lbl_status.config(
            text=(
                "Relatório impresso. "
                "Coloque-o no alimentador ou vidro "
                "e inicie a digitalização."
            )
        )


        # ----------------------------------------------------
        # ATUALMENTE:
        #
        # A comunicação com o scanner ainda não foi ativada.
        #
        # FUTURO:
        #
        # ScanService
        #       ↓
        # scanner da impressora
        #       ↓
        # arquivo digitalizado
        #       ↓
        # visualização
        #
        # ----------------------------------------------------


        if hasattr(
            self,
            "btn_digitalizar",
        ):

            self.btn_digitalizar.config(
                state="normal"
            )

            return


        self.btn_digitalizar = ttk.Button(
            self.master,
        )


        # O botão é criado dentro do mesmo container
        # dos botões da janela.

        # Recuperamos o frame através do parent
        # do botão de impressão.

        botoes = self.btn_imprimir.master


        self.btn_digitalizar = ttk.Button(
            botoes,
            text="INICIAR DIGITALIZAÇÃO",
            command=self._iniciar_digitalizacao,
        )


        self.btn_digitalizar.grid(
            row=0,
            column=2,
            padx=(15, 0),
        )


    # ========================================================
    # INICIAR DIGITALIZAÇÃO
    # ========================================================

    def _iniciar_digitalizacao(self):

        """
        Ponto de entrada da futura integração com ScanService.

        Não inventamos aqui uma comunicação com o scanner.
        """

        self.lbl_status.config(
            text=(
                "Integração do scanner ainda "
                "não foi ativada."
            )
        )


        messagebox.showinfo(
            "Digitalização",
            (
                "O relatório já foi impresso.\n\n"
                "A integração com o scanner será "
                "ativada na próxima etapa."
            ),
            parent=self,
        )