"""
============================================================
PRINTER ASSISTANT — UTILITÁRIOS DE JANELAS (WINDOWS / TKINTER)
============================================================

Corrige definitivamente problemas clássicos de foco, Alt+Tab e
restauração pela barra de tarefas do Tkinter no Windows 10/11:
  - Localiza Toplevels filhos RECURSIVAMENTE (inclusive os criados
    com parent=PrinterView ou outros Frames, não só filhos diretos
    de root);
  - Usa Win32 API (ctypes.windll.user32) para detectar e restaurar
    janelas realmente minimizadas (IsIconic) ou fora da tela
    (-32000, -32000), onde root.state() do Tk frequentemente mente;
  - Evita alterar -topmost dentro de <Activate>/<FocusIn>, que
    conflita com o DWM do Windows e deixa a janela presa na barra
    de tarefas;
  - Garante liberação de grab_set() e devolução limpa de foco ao
    fechar qualquer diálogo modal.
============================================================
"""

import ctypes
from ctypes import wintypes
import os
import tkinter as tk


_IS_WINDOWS = os.name == "nt"
_SW_SHOW = 5
_SW_RESTORE = 9


def _hwnd_real(janela):
    """Retorna o HWND top-level real da janela Tkinter no Windows."""
    if not _IS_WINDOWS or janela is None:
        return 0
    try:
        if not janela.winfo_exists():
            return 0
        hwnd = int(janela.winfo_id())
        if not hwnd:
            return 0
        pai = ctypes.windll.user32.GetParent(hwnd)
        return int(pai) if pai else hwnd
    except Exception:
        return 0


def _garantir_visivel_na_tela(janela):
    """
    Se a janela ficou presa em coordenadas fora da tela (ex.: -32000, -32000
    típico do bug de minimização do Windows/Tk), traz de volta para a área visível.
    """
    if not _IS_WINDOWS or janela is None:
        return
    try:
        if not janela.winfo_exists():
            return
        hwnd = _hwnd_real(janela)
        if not hwnd:
            return
        user32 = ctypes.windll.user32
        if user32.IsIconic(hwnd):
            return
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return
        # Virtual screen bounds (suporta múltiplos monitores)
        vx = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
        vy = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        vw = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
        vh = user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
        if vw <= 0 or vh <= 0:
            return
        fora_x = rect.right < vx + 40 or rect.left > vx + vw - 40
        fora_y = rect.bottom < vy + 40 or rect.top > vy + vh - 40
        if fora_x or fora_y:
            larg = max(janela.winfo_width(), 900)
            alt = max(janela.winfo_height(), 650)
            sw = janela.winfo_screenwidth()
            sh = janela.winfo_screenheight()
            nx = max(20, (sw - larg) // 2)
            ny = max(20, (sh - alt) // 2)
            janela.geometry(f"+{nx}+{ny}")
    except Exception:
        pass


def _restaurar_win32(janela):
    """Restaura uma janela Tkinter usando Win32 ShowWindow quando minimizada/oculta."""
    if janela is None:
        return
    try:
        if not janela.winfo_exists():
            return
        st = janela.state()
        if st in ("iconic", "withdrawn"):
            janela.deiconify()
        if _IS_WINDOWS:
            hwnd = _hwnd_real(janela)
            if hwnd:
                user32 = ctypes.windll.user32
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, _SW_RESTORE)
                elif not user32.IsWindowVisible(hwnd):
                    user32.ShowWindow(hwnd, _SW_SHOW)
                _garantir_visivel_na_tela(janela)
                user32.BringWindowToTop(hwnd)
        janela.lift()
    except Exception:
        pass


def _obter_toplevels_ativos(widget):
    """
    Retorna lista de todas as janelas tk.Toplevel filhas ainda vivas,
    buscando RECURSIVAMENTE em toda a árvore de widgets (inclusive modais
    criados com parent=PrinterView ou outros Frames).
    """
    ativos = []
    if widget is None:
        return ativos

    def _visitar(atual):
        try:
            filhos = atual.winfo_children()
        except tk.TclError:
            return
        for filho in filhos:
            try:
                if not filho.winfo_exists():
                    continue
                if isinstance(filho, tk.Toplevel):
                    ativos.append(filho)
                _visitar(filho)
            except tk.TclError:
                continue

    _visitar(widget)
    return ativos


def trazer_para_frente(janela):
    """Traz uma janela Tkinter para frente de forma segura no Windows."""
    if janela is None:
        return
    try:
        if not janela.winfo_exists():
            return
        _restaurar_win32(janela)
        janela.focus_set()
    except tk.TclError:
        pass


def instalar_protecao_alt_tab(root):
    """
    Instala handlers na janela principal (MainWindow) para garantir que
    Alt+Tab e cliques na barra de tarefas sempre restaurem o aplicativo
    e eventuais diálogos modais abertos sem travar a janela na barra de tarefas.
    """
    estado = {"agendado": False}

    def _executar_restauracao():
        estado["agendado"] = False
        try:
            if not root.winfo_exists():
                return

            filhos = _obter_toplevels_ativos(root)

            # Libera eventual grab órfão (de janela já destruída) que travaria a barra de tarefas
            try:
                atual = root.grab_current()
                if atual is not None:
                    if (not atual.winfo_exists()) or (atual is not root and atual not in filhos):
                        atual.grab_release()
            except tk.TclError:
                pass

            # Restaura a janela principal se estiver minimizada/fora da tela
            _restaurar_win32(root)

            if filhos:
                for f in filhos:
                    _restaurar_win32(f)
                topo = filhos[-1]
                try:
                    topo.lift()
                    topo.focus_set()
                except tk.TclError:
                    pass
        except tk.TclError:
            pass

    def _agendar_restauracao(event=None):
        if event is not None and event.widget is not root:
            return
        if estado["agendado"]:
            return
        estado["agendado"] = True
        try:
            root.after_idle(_executar_restauracao)
        except tk.TclError:
            estado["agendado"] = False

    # <Map> dispara ao restaurar da barra de tarefas; <Activate> ao clicar no ícone / Alt+Tab.
    # Executamos via after_idle para não brigar com o WM_ACTIVATE/DWM do Windows.
    root.bind("<Map>", _agendar_restauracao, add="+")
    root.bind("<Activate>", _agendar_restauracao, add="+")


def configurar_modal(janela, parent, modal=True):
    """
    Configura corretamente um Toplevel no Windows:
      - transient() sempre apontando para parent.winfo_toplevel() (nunca um Frame);
      - garante que a janela mãe esteja restaurada/visível;
      - grab_set() opcional com liberação garantida ao fechar;
      - se o usuário clicar na janela principal ou voltar via Alt+Tab,
        restaura o modal corretamente em vez de travar o aplicativo.
    """
    dono = None
    if parent is not None:
        try:
            dono = parent.winfo_toplevel()
        except tk.TclError:
            dono = None

    if dono is not None:
        try:
            _restaurar_win32(dono)
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
                    dono.after_idle(lambda a=alvo: trazer_para_frente(a))
            except tk.TclError:
                pass

    janela.bind("<Destroy>", _ao_destruir, add="+")

    try:
        janela.lift()
        janela.focus_set()
    except tk.TclError:
        pass
