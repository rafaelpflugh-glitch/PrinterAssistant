"""
============================================================
PRINTER ASSISTANT — UTILITÁRIOS DE JANELAS (WINDOWS / TKINTER)
============================================================

Corrige problemas clássicos de foco e Alt+Tab do Tkinter no Windows:
  - Garante que .transient() receba sempre o toplevel real (nunca um Frame);
  - Evita que janelas modais com grab_set() fiquem presas atrás de outros apps
    ao usar Alt+Tab ou clicar na barra de tarefas;
  - Garante liberação de grab e devolução de foco ao fechar qualquer modal;
  - Ao restaurar/focar a janela principal via Alt+Tab, traz automaticamente
    qualquer diálogo filho aberto para a frente.
============================================================
"""

import tkinter as tk


def _obter_toplevels_ativos(root):
    """Retorna lista de janelas Toplevel filhas ainda vivas e visíveis."""
    ativos = []
    if root is None:
        return ativos
    try:
        for filho in root.winfo_children():
            if isinstance(filho, tk.Toplevel) and filho.winfo_exists():
                ativos.append(filho)
    except tk.TclError:
        pass
    return ativos


def trazer_para_frente(janela):
    """Traz uma janela Tkinter para frente de forma segura no Windows."""
    if janela is None:
        return
    try:
        if not janela.winfo_exists():
            return
        if janela.state() == "iconic":
            janela.deiconify()
        janela.lift()
        janela.focus_force()
    except tk.TclError:
        pass


def instalar_protecao_alt_tab(root):
    """
    Instala handlers na janela principal (MainWindow) para garantir que
    Alt+Tab e cliques na barra de tarefas sempre tragam o aplicativo
    (e eventuais diálogos modais abertos) de volta para a tela.
    """
    estado = {"restaurando": False}

    def _restaurar_foco(event=None):
        if event is not None and event.widget is not root:
            return
        if estado["restaurando"]:
            return

        estado["restaurando"] = True
        try:
            if not root.winfo_exists():
                return

            filhos = _obter_toplevels_ativos(root)
            if filhos:
                # Se há diálogo modal/preview aberto, traz o mais recente para cima
                topo = filhos[-1]
                try:
                    if topo.state() == "iconic":
                        topo.deiconify()
                    topo.lift()
                    topo.focus_force()
                except tk.TclError:
                    pass
            else:
                # Libera eventual grab órfão que possa travar o foco
                try:
                    atual = root.grab_current()
                    if atual is not None and (not atual.winfo_exists() or atual is not root):
                        atual.grab_release()
                except tk.TclError:
                    pass

                # Garante que a janela principal venha para a frente no Z-order do Windows
                try:
                    if root.state() == "iconic":
                        root.deiconify()
                    root.lift()
                except tk.TclError:
                    pass
        finally:
            try:
                root.after(120, lambda: estado.__setitem__("restaurando", False))
            except tk.TclError:
                estado["restaurando"] = False

    root.bind("<Map>", _restaurar_foco, add="+")
    root.bind("<FocusIn>", _restaurar_foco, add="+")
    root.bind("<Activate>", _restaurar_foco, add="+")


def configurar_modal(janela, parent, modal=True):
    """
    Configura corretamente um Toplevel no Windows:
      - transient() sempre apontando para parent.winfo_toplevel() (nunca um Frame);
      - grab_set() opcional com liberação garantida ao fechar;
      - devolve foco e lift para a janela principal ao ser destruído.
    """
    dono = None
    if parent is not None:
        try:
            dono = parent.winfo_toplevel()
        except tk.TclError:
            dono = None

    if dono is not None:
        try:
            janela.transient(dono)
        except tk.TclError:
            pass

    if modal:
        try:
            janela.grab_set()
        except tk.TclError:
            pass

    def _ao_destruir(event=None):
        if event is not None and event.widget is not janela:
            return
        try:
            janela.grab_release()
        except tk.TclError:
            pass
        if dono is not None:
            try:
                if dono.winfo_exists():
                    outros = [f for f in _obter_toplevels_ativos(dono) if f is not janela]
                    alvo = outros[-1] if outros else dono
                    dono.after(10, lambda a=alvo: _reativar_alvo(a))
            except tk.TclError:
                pass

    def _reativar_alvo(alvo):
        try:
            if alvo.winfo_exists():
                if alvo.state() == "iconic":
                    alvo.deiconify()
                alvo.lift()
                alvo.focus_set()
        except tk.TclError:
            pass

    janela.bind("<Destroy>", _ao_destruir, add="+")

    try:
        janela.lift()
        janela.focus_force()
    except tk.TclError:
        pass
