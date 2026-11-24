"""
============================================================
ASSISTENTE DE IMPRESSORAS - PAINEL DE CONFIGURAÇÕES
============================================================
Janela de configuração dos IPs Padrão e Exceção para cada
tipo de etiquetadora térmica (Produção, RMA e Ativo).
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.config import carregar_config, salvar_config


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configurações do Sistema")
        self.geometry("640x740")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.config_data = carregar_config()
        self._criar_interface()

    def _criar_interface(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        # Cabeçalho
        ttk.Label(
            container,
            text="Roteamento de Impressoras Térmicas",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            container,
            text="Configure o IP Padrão e o IP de Exceção/Redirecionamento para cada etiquetadora.",
            font=("Segoe UI", 9),
            foreground="#aaaaaa",
        ).pack(anchor="w", pady=(0, 15))

        # ====================================================
        # 1. ETIQUETADORA DE PRODUÇÃO
        # ====================================================
        grp_prod = ttk.LabelFrame(
            container, text=" 1. Etiquetadora de Produção (50x38mm) ", padding=12
        )
        grp_prod.pack(fill="x", pady=(0, 12))

        grid_prod = ttk.Frame(grp_prod)
        grid_prod.pack(fill="x")

        ttk.Label(grid_prod, text="IP Padrão:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_prod_padrao = ttk.Entry(grid_prod, width=18)
        self.entry_prod_padrao.grid(row=0, column=1, sticky="w", padx=(5, 20), pady=4)
        self.entry_prod_padrao.insert(
            0, self.config_data.get("producao_ip_padrao", "192.168.14.111")
        )

        ttk.Label(grid_prod, text="IP de Exceção:").grid(row=0, column=2, sticky="w", pady=4)
        self.entry_prod_excecao = ttk.Entry(grid_prod, width=18)
        self.entry_prod_excecao.grid(row=0, column=3, sticky="w", padx=(5, 0), pady=4)
        self.entry_prod_excecao.insert(
            0, self.config_data.get("producao_ip_excecao", "192.168.14.151")
        )

        self.var_prod_excecao = tk.BooleanVar(
            value=self.config_data.get("producao_usar_excecao", True)
        )
        ttk.Checkbutton(
            grp_prod,
            text="Ativar Exceção (Redirecionar impressões de Produção para o IP de Exceção)",
            variable=self.var_prod_excecao,
        ).pack(anchor="w", pady=(6, 0))

        # ====================================================
        # 2. ETIQUETADORA DE RMA / UST
        # ====================================================
        grp_rma = ttk.LabelFrame(
            container, text=" 2. Etiquetadora de RMA / UST (100x150mm) ", padding=12
        )
        grp_rma.pack(fill="x", pady=(0, 12))

        grid_rma = ttk.Frame(grp_rma)
        grid_rma.pack(fill="x")

        ttk.Label(grid_rma, text="IP Padrão:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_rma_padrao = ttk.Entry(grid_rma, width=18)
        self.entry_rma_padrao.grid(row=0, column=1, sticky="w", padx=(5, 20), pady=4)
        self.entry_rma_padrao.insert(
            0, self.config_data.get("rma_ip_padrao", "192.168.14.151")
        )

        ttk.Label(grid_rma, text="IP de Exceção:").grid(row=0, column=2, sticky="w", pady=4)
        self.entry_rma_excecao = ttk.Entry(grid_rma, width=18)
        self.entry_rma_excecao.grid(row=0, column=3, sticky="w", padx=(5, 0), pady=4)
        self.entry_rma_excecao.insert(
            0, self.config_data.get("rma_ip_excecao", "192.168.14.151")
        )

        self.var_rma_excecao = tk.BooleanVar(
            value=self.config_data.get("rma_usar_excecao", False)
        )
        ttk.Checkbutton(
            grp_rma,
            text="Ativar Exceção (Redirecionar impressões de RMA para o IP de Exceção)",
            variable=self.var_rma_excecao,
        ).pack(anchor="w", pady=(6, 0))

        # ====================================================
        # 3. ETIQUETADORA DE ATIVO PATRIMONIAL
        # ====================================================
        grp_ativo = ttk.LabelFrame(
            container, text=" 3. Etiquetadora de Ativo Patrimonial (100x150mm) ", padding=12
        )
        grp_ativo.pack(fill="x", pady=(0, 15))

        grid_ativo = ttk.Frame(grp_ativo)
        grid_ativo.pack(fill="x")

        ttk.Label(grid_ativo, text="IP Padrão:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_ativo_padrao = ttk.Entry(grid_ativo, width=18)
        self.entry_ativo_padrao.grid(row=0, column=1, sticky="w", padx=(5, 20), pady=4)
        self.entry_ativo_padrao.insert(
            0, self.config_data.get("ativo_ip_padrao", "192.168.14.151")
        )

        ttk.Label(grid_ativo, text="IP de Exceção:").grid(row=0, column=2, sticky="w", pady=4)
        self.entry_ativo_excecao = ttk.Entry(grid_ativo, width=18)
        self.entry_ativo_excecao.grid(row=0, column=3, sticky="w", padx=(5, 0), pady=4)
        self.entry_ativo_excecao.insert(
            0, self.config_data.get("ativo_ip_excecao", "192.168.14.151")
        )

        self.var_ativo_excecao = tk.BooleanVar(
            value=self.config_data.get("ativo_usar_excecao", False)
        )
        ttk.Checkbutton(
            grp_ativo,
            text="Ativar Exceção (Redirecionar impressões de Ativo para o IP de Exceção)",
            variable=self.var_ativo_excecao,
        ).pack(anchor="w", pady=(6, 0))

        # ====================================================
        # 4. BASE DE DADOS DE PART NUMBERS (GESTOR CPA)
        # ====================================================
        grp_base = ttk.LabelFrame(
            container, text=" 4. Base de Dados de Part Numbers (Gestor CPA - Somente Leitura) ", padding=12
        )
        grp_base.pack(fill="x", pady=(0, 15))

        ttk.Label(grp_base, text="Pasta / Planilha na Rede:").pack(anchor="w", pady=(0, 4))
        self.entry_base_pn = ttk.Entry(grp_base)
        self.entry_base_pn.pack(fill="x", pady=(0, 6))
        self.entry_base_pn.insert(
            0,
            self.config_data.get(
                "caminho_base_pn", r"W:\TEC\Banco de Dados_Gestor de Part Number"
            ),
        )

        status_txt = "Verificando conexão com a base..."
        status_cor = "#aaaaaa"
        try:
            from core.planilha_pn import status_base_pn
            st = status_base_pn(self.entry_base_pn.get().strip())
            if st.get("conectado"):
                status_txt = f"Conectado: {st['total_itens']} registros disponíveis (atualização automática)."
                status_cor = "#4ade80"
            else:
                status_txt = "Rede indisponível no momento — usando tabela interna de backup."
                status_cor = "#f59e0b"
        except Exception:
            status_txt = "Usando tabela interna de backup."

        ttk.Label(
            grp_base,
            text=status_txt,
            font=("Segoe UI", 8),
            foreground=status_cor,
        ).pack(anchor="w")

        # ====================================================
        # BOTOES
        # ====================================================
        botoes = ttk.Frame(container)
        botoes.pack(anchor="e", pady=(5, 0))

        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(
            side="left", padx=6
        )
        ttk.Button(botoes, text="Salvar Alterações", command=self._salvar).pack(
            side="left"
        )

    def _salvar(self):
        prod_p = self.entry_prod_padrao.get().strip()
        prod_e = self.entry_prod_excecao.get().strip()

        rma_p = self.entry_rma_padrao.get().strip()
        rma_e = self.entry_rma_excecao.get().strip()

        ativo_p = self.entry_ativo_padrao.get().strip()
        ativo_e = self.entry_ativo_excecao.get().strip()

        if not all([prod_p, prod_e, rma_p, rma_e, ativo_p, ativo_e]):
            messagebox.showwarning(
                "Aviso", "Todos os campos de IP Padrão e Exceção devem ser preenchidos.", parent=self
            )
            return

        self.config_data["producao_ip_padrao"] = prod_p
        self.config_data["producao_ip_excecao"] = prod_e
        self.config_data["producao_usar_excecao"] = self.var_prod_excecao.get()

        self.config_data["rma_ip_padrao"] = rma_p
        self.config_data["rma_ip_excecao"] = rma_e
        self.config_data["rma_usar_excecao"] = self.var_rma_excecao.get()

        self.config_data["ativo_ip_padrao"] = ativo_p
        self.config_data["ativo_ip_excecao"] = ativo_e
        self.config_data["ativo_usar_excecao"] = self.var_ativo_excecao.get()

        caminho_pn = self.entry_base_pn.get().strip()
        if caminho_pn:
            self.config_data["caminho_base_pn"] = caminho_pn

        if salvar_config(self.config_data):
            messagebox.showinfo(
                "Sucesso",
                "Configurações de Padrão e Exceção salvas com sucesso!",
                parent=self,
            )
            self.destroy()
        else:
            messagebox.showerror(
                "Erro", "Falha ao salvar o arquivo config.json.", parent=self
            )