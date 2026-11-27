"""
============================================================
PRINTER ASSISTANT — DIÁLOGO DE ATUALIZAÇÃO
(interface/update_dialog.py)
============================================================
Exibe detalhes da nova versão disponível (GitHub Releases ou Git),
barra de progresso durante o download/pull e executa a atualização
com segurança preservando as configurações do usuário.
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from core.updater import (
    UpdateInfo,
    aplicar_atualizacao_exe,
    aplicar_atualizacao_git,
    iniciar_script_atualizacao_exe,
    reiniciar_aplicacao_python,
)


class UpdateDialog(tk.Toplevel):

    def __init__(self, parent, info: UpdateInfo):
        super().__init__(parent)
        self.parent = parent
        self.info = info
        self._atualizando = False

        self.title("Atualização do Printer Assistant")
        self.geometry("560x410")
        self.resizable(False, False)

        from interface.window_utils import configurar_modal
        configurar_modal(self, parent, modal=True)

        self._criar_interface()

    def _criar_interface(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        modo_label = {
            "exe": "Executável (GitHub Releases)",
            "git": "Repositório Git (origin/main)",
            "zip_manual": "Pacote ZIP (GitHub Releases)",
        }.get(self.info.modo, self.info.modo)

        ttk.Label(
            container,
            text="Nova atualização disponível",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=(
                f"Versão atual: {self.info.versao_atual}   →   "
                f"Disponível: {self.info.nova_versao}   |   Modo: {modo_label}"
            ),
            font=("Segoe UI", 9),
            foreground="#aaaaaa",
        ).pack(anchor="w", pady=(4, 12))

        # Caixa com notas da versão / commits
        frame_notas = ttk.LabelFrame(container, text=" O que há de novo ", padding=8)
        frame_notas.pack(fill="both", expand=True, pady=(0, 12))

        self.txt_notas = tk.Text(
            frame_notas,
            height=9,
            wrap="word",
            bg="#18181b",
            fg="#e4e4e7",
            relief="flat",
            font=("Segoe UI", 9),
            padx=6,
            pady=6,
        )
        self.txt_notas.pack(fill="both", expand=True)
        self.txt_notas.insert("1.0", self.info.notas or "Melhorias e correções gerais.")
        self.txt_notas.config(state="disabled")

        # Progresso
        self.lbl_progresso = ttk.Label(
            container,
            text="Suas configurações locais (config.json e logs) serão preservadas.",
            font=("Segoe UI", 9),
        )
        self.lbl_progresso.pack(anchor="w", pady=(0, 6))

        self.progress = ttk.Progressbar(container, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 14))

        # Botões
        botoes = ttk.Frame(container)
        botoes.pack(fill="x")

        self.btn_fechar = ttk.Button(
            botoes,
            text="Depois",
            command=self._fechar,
        )
        self.btn_fechar.pack(side="right")

        pode_auto = (
            self.info.modo == "git"
            or (self.info.modo == "exe" and bool(self.info.download_url))
        )

        if pode_auto:
            self.btn_atualizar = ttk.Button(
                botoes,
                text="Atualizar agora",
                command=self._iniciar_atualizacao,
            )
            self.btn_atualizar.pack(side="right", padx=(0, 8))
        else:
            self.btn_atualizar = ttk.Button(
                botoes,
                text="Abrir página no GitHub",
                command=lambda: webbrowser.open(self.info.release_url),
            )
            self.btn_atualizar.pack(side="right", padx=(0, 8))

    def _fechar(self):
        if not self._atualizando:
            self.destroy()

    def _atualizar_ui_progresso(self, pct: int, msg: str):
        try:
            self.progress["value"] = max(0, min(100, pct))
            self.lbl_progresso.config(text=msg)
        except Exception:
            pass

    def _iniciar_atualizacao(self):
        if self._atualizando:
            return
        self._atualizando = True
        self.btn_atualizar.config(state="disabled")
        self.btn_fechar.config(state="disabled")

        threading.Thread(target=self._executar_worker, daemon=True).start()

    def _executar_worker(self):
        def _cb(pct: int, msg: str):
            self.after(0, lambda p=pct, m=msg: self._atualizar_ui_progresso(p, m))

        if self.info.modo == "git":
            ok, msg = aplicar_atualizacao_git(on_progress=_cb)
            self.after(0, lambda: self._concluir_git(ok, msg))
        else:
            ok, msg, bat_path = aplicar_atualizacao_exe(self.info, on_progress=_cb)
            self.after(0, lambda: self._concluir_exe(ok, msg, bat_path))

    def _concluir_git(self, ok: bool, msg: str):
        self._atualizando = False
        if not ok:
            self.btn_atualizar.config(state="normal")
            self.btn_fechar.config(state="normal")
            messagebox.showerror("Atualização", msg, parent=self)
            return

        messagebox.showinfo("Atualização concluída", msg, parent=self)
        try:
            reiniciar_aplicacao_python()
        finally:
            self.destroy()
            self.parent.destroy()

    def _concluir_exe(self, ok: bool, msg: str, bat_path):
        self._atualizando = False
        if not ok or bat_path is None:
            self.btn_atualizar.config(state="normal")
            self.btn_fechar.config(state="normal")
            messagebox.showerror("Atualização", msg, parent=self)
            return

        messagebox.showinfo("Atualização pronta", msg, parent=self)
        iniciar_script_atualizacao_exe(bat_path)
        self.destroy()
        self.parent.destroy()
