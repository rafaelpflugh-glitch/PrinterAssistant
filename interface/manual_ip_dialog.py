"""
============================================================
PRINTER ASSISTANT - DIÁLOGO DE IP MANUAL COM HISTÓRICO
============================================================
Permite ao técnico informar um IP manualmente para identificação direta
ou selecionar rapidamente um dos IPs utilizados recentemente.
============================================================
"""

import ipaddress
import tkinter as tk
from tkinter import ttk, messagebox

from core.config import carregar_ips_recentes, salvar_ip_recente


class ManualIPDialog(tk.Toplevel):
    """
    Diálogo modal para inserção manual de IP com histórico dropdown.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.resultado = None

        self.title("Adicionar IP Manual")
        self.geometry("480x250")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.ips_recentes = carregar_ips_recentes()

        self._criar_interface()
        self._centralizar(parent)

        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self.bind("<Escape>", lambda e: self._cancelar())
        self.bind("<Return>", lambda e: self._confirmar())

    def _centralizar(self, parent):
        self.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - 480) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - 250) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _criar_interface(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        # Cabeçalho
        ttk.Label(
            container,
            text="Adicionar Impressora por IP",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            container,
            text="Digite o endereço IP da impressora ou escolha um IP recente:",
            font=("Segoe UI", 9),
            foreground="#9AA3AD",
        ).pack(anchor="w", pady=(0, 15))

        # Campo com Combobox
        form_frame = ttk.Frame(container)
        form_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            form_frame,
            text="Endereço IP:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        self.combo_ip = ttk.Combobox(
            form_frame,
            values=self.ips_recentes,
            font=("Consolas", 11),
        )
        self.combo_ip.pack(fill="x", ipady=4)

        if self.ips_recentes:
            self.combo_ip.set(self.ips_recentes[0])

        self.combo_ip.focus_set()
        self.combo_ip.select_range(0, tk.END)

        ttk.Label(
            form_frame,
            text="Exemplo: 192.168.14.152  (Use a seta para ver o histórico)",
            font=("Segoe UI", 8),
            foreground="#6E7681",
        ).pack(anchor="w", pady=(4, 0))

        # Botões
        botoes = ttk.Frame(container)
        botoes.pack(fill="x", side="bottom")

        self.btn_cancelar = ttk.Button(
            botoes,
            text="Cancelar",
            command=self._cancelar,
        )
        self.btn_cancelar.pack(side="right", padx=(8, 0))

        self.btn_confirmar = ttk.Button(
            botoes,
            text="Identificar Impressora",
            command=self._confirmar,
        )
        self.btn_confirmar.pack(side="right")

    def _confirmar(self):
        ip_texto = self.combo_ip.get().strip()

        if not ip_texto:
            messagebox.showwarning(
                "Atenção",
                "Por favor, digite ou selecione um endereço IP.",
                parent=self,
            )
            self.combo_ip.focus_set()
            return

        try:
            ipaddress.ip_address(ip_texto)
        except ValueError:
            messagebox.showerror(
                "IP Inválido",
                f"O endereço '{ip_texto}' não é um IPv4 válido.\nExemplo de formato: 192.168.1.100",
                parent=self,
            )
            self.combo_ip.focus_set()
            return

        # Salva no histórico de recentes
        salvar_ip_recente(ip_texto)

        self.resultado = ip_texto
        self.destroy()

    def _cancelar(self):
        self.resultado = None
        self.destroy()
