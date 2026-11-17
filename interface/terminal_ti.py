import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import webbrowser
import asyncio

# ==========================================
# IMPORTAÇÃO SEGURA PYSNMP v7+ 
# ==========================================
try:
    from pysnmp.hlapi.v3arch.asyncio import (
        set_cmd, SnmpEngine, CommunityData, UdpTransportTarget, 
        ContextData, ObjectType, ObjectIdentity, OctetString
    )
    HAS_PYSNMP = True
except ImportError:
    HAS_PYSNMP = False

class TerminalTIWindow(tk.Toplevel):
    # Paleta de Cores (Dark UI - Estilo VS Code)
    COR_FUNDO = "#121417"
    COR_PAINEL = "#1a1d23"
    COR_PAINEL_2 = "#21262d"
    COR_BORDA = "#30363d"
    COR_TEXTO = "#e6edf3"
    COR_TEXTO_SECUNDARIO = "#8b949e"
    COR_DESTAQUE = "#58a6ff"
    COR_VERDE = "#3fb950"

    def __init__(self, master=None, device=None):
        if master: 
            super().__init__(master)
            self.transient(master)
        else:
            super().__init__()
            
        self.device = device
        self.title("Terminal TI — Painel Operacional Lexmark MX611")
        self.geometry("1400x950")
        self.minsize(1024, 768)
        self.configure(background=self.COR_FUNDO)

        self.ip_alvo = "192.168.14.134"
        if self.device:
            dev_ip = getattr(self.device, "ip", "")
            if not dev_ip and hasattr(self.device, "to_dict"):
                try: dev_ip = self.device.to_dict().get("ip", "")
                except Exception: pass
            if dev_ip: self.ip_alvo = dev_ip

        self._criar_estilos()
        self._criar_interface()

    def _criar_estilos(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        
        style.configure("TFrame", background=self.COR_FUNDO)
        style.configure("TLabel", background=self.COR_FUNDO, foreground=self.COR_TEXTO, font=("Segoe UI", 9))
        style.configure("TNotebook", background=self.COR_FUNDO, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.COR_PAINEL_2, foreground=self.COR_TEXTO_SECUNDARIO, padding=[12, 8], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", self.COR_PAINEL)], foreground=[("selected", self.COR_DESTAQUE)])

        style.configure("Acao.TButton", background="#1f6feb", foreground="#ffffff", bordercolor="#388bfd", padding=7, font=("Segoe UI", 9, "bold"))
        style.map("Acao.TButton", background=[("active", "#388bfd"), ("pressed", "#1158c7")])
        
        style.configure("Alerta.TButton", background="#da3633", foreground="#ffffff", bordercolor="#f85149", padding=7, font=("Segoe UI", 9, "bold"))
        style.map("Alerta.TButton", background=[("active", "#f85149")])

    def _criar_interface(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # TOPO: CONEXÃO UNIVERSAL
        topo = tk.Frame(self, background=self.COR_PAINEL, padx=15, pady=12, highlightbackground=self.COR_BORDA, highlightthickness=1)
        topo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        topo.columnconfigure(4, weight=1)

        ttk.Label(topo, text="IP da Impressora:", background=self.COR_PAINEL, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(0, 5))
        self.entry_ip = ttk.Entry(topo, font=("Segoe UI", 10, "bold"), width=16)
        self.entry_ip.insert(0, self.ip_alvo)
        self.entry_ip.grid(row=0, column=1, padx=(0, 15))

        ttk.Label(topo, text="Comunidade SNMP:", background=self.COR_PAINEL).grid(row=0, column=2, padx=(0, 5))
        self.combo_comunidade = ttk.Combobox(topo, values=("public", "private", "admin"), width=10, state="readonly")
        self.combo_comunidade.set("private")
        self.combo_comunidade.grid(row=0, column=3, padx=(0, 15))

        ttk.Button(topo, text="🌐 ABRIR PAINEL WEB", command=lambda: webbrowser.open(f"http://{self.entry_ip.get()}"), style="Acao.TButton").grid(row=0, column=5)

        # CORPO: ABAS ESQUERDA / CONSOLE DIREITA
        corpo = tk.Frame(self, background=self.COR_FUNDO)
        corpo.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        corpo.columnconfigure(0, weight=6)
        corpo.columnconfigure(1, weight=4)
        corpo.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(corpo)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self._aba_editor_variaveis()
        self._aba_display_mensagens()
        self._aba_identidade_snmp()
        self._aba_dicionario_completo()
        self._aba_terminal_livre()

        # CONSOLE DE RESPOSTAS
        console_frame = tk.Frame(corpo, background=self.COR_PAINEL, highlightbackground=self.COR_BORDA, highlightthickness=1)
        console_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(1, weight=1)

        h_console = tk.Frame(console_frame, background=self.COR_PAINEL, padx=10, pady=8)
        h_console.grid(row=0, column=0, sticky="ew")
        h_console.columnconfigure(0, weight=1)
        tk.Label(h_console, text="LOGS E RETORNO DA PLACA", background=self.COR_PAINEL, foreground=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(h_console, text="Limpar", command=lambda: self.txt_console.delete("1.0", "end"), style="Acao.TButton").grid(row=0, column=1, sticky="e")

        self.txt_console = scrolledtext.ScrolledText(console_frame, wrap="word", font=("Consolas", 9), background="#0d1117", foreground=self.COR_VERDE, borderwidth=0, padx=10, pady=10)
        self.txt_console.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.txt_console.insert("end", f"Painel Operacional Lexmark ativo no IP {self.ip_alvo}\n\n")

    def _criar_aba_rolavel(self, nome_aba):
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text=nome_aba)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        canvas = tk.Canvas(f, background=self.COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, background=self.COR_FUNDO)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollable_frame.columnconfigure(0, weight=1)
        return scrollable_frame

    def _log(self, texto):
        self.txt_console.insert("end", f"{texto}\n")
        self.txt_console.see("end")

    # ==========================================
    # MOTORES DE COMUNICAÇÃO
    # ==========================================
    def _executar_snmp_set(self, oid, valor, descricao):
        if not HAS_PYSNMP:
            return messagebox.showerror("Erro", "Biblioteca PySNMP não carregada.")
        ip = self.entry_ip.get().strip()
        comunidade = self.combo_comunidade.get()
        self._log(f"\n--- [SNMP SET] Gravando '{descricao}' ---")

        def tarefa():
            async def run_set():
                try:
                    engine = SnmpEngine()
                    target = await UdpTransportTarget.create((ip, 161), timeout=4.0, retries=1)
                    _, status, _, _ = await set_cmd(
                        engine, CommunityData(comunidade, mpModel=1), target, ContextData(),
                        ObjectType(ObjectIdentity(oid), OctetString(valor))
                    )
                    if status:
                        self.after(0, lambda: self._log(f"Negado: {status.prettyPrint()}\n"))
                    else:
                        self.after(0, lambda: self._log(f"➜ SUCESSO! '{valor}' gravado na NVRAM.\n"))
                except Exception as e:
                    self.after(0, lambda: self._log(f"[ERRO SNMP] {e}\n"))
            asyncio.run(run_set())

        threading.Thread(target=tarefa, daemon=True).start()

    def _enviar_pjl(self, comandos_lista, descricao):
        ip = self.entry_ip.get().strip()
        self._log(f"\n--- [PJL JOB FORMAL] {descricao} ---")
        for c in comandos_lista:
            self._log(f" > DEFAULT {c}")
        
        def tarefa():
            try:
                uel = b"\x1B%-12345X"
                corpo_cmd = f"@PJL JOB NAME=\"PrinterAssistant_TI\"\r\n".encode('utf-8')
                for c in comandos_lista:
                    corpo_cmd += f"@PJL DEFAULT {c.strip()}\r\n".encode('utf-8')
                corpo_cmd += f"@PJL EOJ\r\n".encode('utf-8')
                
                payload = uel + corpo_cmd + uel
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5.0)
                    s.connect((ip, 9100))
                    s.sendall(payload)
                    
                    s.settimeout(2.5)
                    buffer = bytearray()
                    while True:
                        try:
                            chunk = s.recv(4096)
                            if not chunk: break
                            buffer.extend(chunk)
                        except socket.timeout: break
                            
                if buffer:
                    resposta = buffer.decode('utf-8', errors='replace').replace('\x1b%-12345X', '').strip()
                    self.after(0, lambda: self._log(f"➜ RETORNO DA PLACA:\n{resposta if resposta else 'Gravado com sucesso na NVRAM.'}\n"))
                else:
                    self.after(0, lambda: self._log("➜ SUCESSO: Job processado pela controladora.\n"))
            except Exception as e:
                self.after(0, lambda: self._log(f"[ERRO 9100]: {e}\n"))
        
        threading.Thread(target=tarefa, daemon=True).start()

    # ==========================================
    # ABA 1: EDITOR DE VARIÁVEIS HUMANIZADO
    # ==========================================
    def _aba_editor_variaveis(self):
        f = self._criar_aba_rolavel(" 🎛️ Gestão de Mídia & Papel ")
        
        # Bloco 1: Gaveta Principal (Bandeja 1)
        g1 = tk.LabelFrame(f, text=" Configuração Física da Bandeja 1 (INTRAY1 / LTRAY1) ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g1.pack(fill="x", padx=10, pady=10)

        tk.Label(g1, text="Define o tamanho e o tipo de suporte de papel padrão da gaveta principal.", bg=self.COR_PAINEL, fg=self.COR_TEXTO_SECUNDARIO).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        tk.Label(g1, text="Tamanho do Papel (INTRAY1SIZE):", bg=self.COR_PAINEL, fg=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        cb_size = ttk.Combobox(g1, values=("A4", "LETTER", "LEGAL", "A5", "EXECUTIVE", "FOLIO", "OFICIO", "STATEMENT"), width=22, state="readonly")
        cb_size.set("A4")
        cb_size.grid(row=1, column=1, padx=10, pady=6)

        tk.Label(g1, text="Tipo de Mídia (LTRAY1PAPERTYPE):", bg=self.COR_PAINEL, fg=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        cb_type = ttk.Combobox(g1, values=("PLAIN", "CARDSTOCK", "LABELS", "TRANSPARENCY", "BOND", "RECYCLED", "LETTERHEAD"), width=22, state="readonly")
        cb_type.set("PLAIN")
        cb_type.grid(row=2, column=1, padx=10, pady=6)

        def aplicar_bandeja_1():
            comandos = [
                f"INTRAY1SIZE={cb_size.get()}",
                f"LTRAY1PAPERTYPE={cb_type.get()}"
            ]
            self._enviar_pjl(comandos, f"Configurar Bandeja 1 ({cb_size.get()} / {cb_type.get()})")

        ttk.Button(g1, text="⚡ APLICAR NA BANDEJA 1", command=aplicar_bandeja_1, style="Acao.TButton").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        # Bloco 2: Propriedades Avançadas de Textura e Peso (Baseado no seu Dump)
        g2 = tk.LabelFrame(f, text=" Ajuste Fino de Gramatura e Textura (Papel Bond / Cartão) ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g2.pack(fill="x", padx=10, pady=10)

        tk.Label(g2, text="Controla como a impressora aquece o fusor e puxa papéis especiais.", bg=self.COR_PAINEL, fg=self.COR_TEXTO_SECUNDARIO).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        tk.Label(g2, text="Gramatura Papel Bond (LBONDWEIGHT):", bg=self.COR_PAINEL, fg=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        cb_bweight = ttk.Combobox(g2, values=("LIGHT", "NORMAL", "HEAVY"), width=22, state="readonly")
        cb_bweight.set("NORMAL")
        cb_bweight.grid(row=1, column=1, padx=10, pady=6)

        tk.Label(g2, text="Textura Papel Cartão (LCARDSTOCKTEXTURE):", bg=self.COR_PAINEL, fg=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        cb_ctext = ttk.Combobox(g2, values=("SMOOTH", "NORMAL", "ROUGH"), width=22, state="readonly")
        cb_ctext.set("NORMAL")
        cb_ctext.grid(row=2, column=1, padx=10, pady=6)

        def aplicar_ajuste_fino():
            comandos = [
                f"LBONDWEIGHT={cb_bweight.get()}",
                f"LCARDSTOCKTEXTURE={cb_ctext.get()}"
            ]
            self._enviar_pjl(comandos, "Ajuste Fino de Gramatura e Textura")

        ttk.Button(g2, text="⚡ APLICAR AJUSTE FINO", command=aplicar_ajuste_fino, style="Acao.TButton").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        # Bloco 3: Sistema e Desempenho
        g3 = tk.LabelFrame(f, text=" Parâmetros Gerais do Sistema ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g3.pack(fill="x", padx=10, pady=10)

        tk.Label(g3, text="Resolução de Impressão (RESOLUTION):", bg=self.COR_PAINEL, fg=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        cb_res = ttk.Combobox(g3, values=("300", "600", "1200"), width=22, state="readonly")
        cb_res.set("600")
        cb_res.grid(row=1, column=1, padx=10, pady=6)

        tk.Label(g3, text="Modo Frente e Verso (DUPLEX):", bg=self.COR_PAINEL, fg=self.COR_TEXTO, font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        cb_duplex = ttk.Combobox(g3, values=("ON", "OFF"), width=22, state="readonly")
        cb_duplex.set("OFF")
        cb_duplex.grid(row=2, column=1, padx=10, pady=6)

        def aplicar_sistema():
            comandos = [
                f"RESOLUTION={cb_res.get()}",
                f"DUPLEX={cb_duplex.get()}"
            ]
            self._enviar_pjl(comandos, "Parâmetros Gerais do Sistema")

        ttk.Button(g3, text="⚡ APLICAR SISTEMA", command=aplicar_sistema, style="Acao.TButton").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    # ==========================================
    # ABA 2: DISPLAY ECRÃ
    # ==========================================
    def _aba_display_mensagens(self):
        f = self._criar_aba_rolavel(" 🖥️ Tela Frontal ")
        g1 = tk.LabelFrame(f, text=" Mensagem Personalizada no Display (LCD) ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g1.pack(fill="x", padx=10, pady=10)

        e_msg = ttk.Entry(g1, width=45, font=("Segoe UI", 10)); e_msg.insert(0, "Suporte TI - Ramal 1234")
        e_msg.pack(side="left", padx=(0, 10))

        ttk.Button(g1, text="⚡ INJETAR MENSAGEM", command=lambda: self._enviar_pjl([f'RDYMSG DISPLAY="{e_msg.get()}"'], "Alterar Display LCD"), style="Acao.TButton").pack(side="left")
        ttk.Button(g1, text="🧹 RESTAURAR PADRÃO", command=lambda: self._enviar_pjl(['RDYMSG DISPLAY=""'], "Restaurar LCD Padrão"), style="Alerta.TButton").pack(side="left", padx=(10, 0))

    # ==========================================
    # ABA 3: IDENTIDADE SNMP
    # ==========================================
    def _aba_identidade_snmp(self):
        f = self._criar_aba_rolavel(" 🏷️ Identidade de Rede ")
        g1 = tk.LabelFrame(f, text=" Gravação de Nome e Localização via SNMP SET ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g1.pack(fill="x", padx=10, pady=10)

        ttk.Label(g1, text="Nome da Máquina (sysName):").grid(row=0, column=0, sticky="w", pady=6)
        e_name = ttk.Entry(g1, width=32); e_name.insert(0, "TI-LEXMARK-MX611")
        e_name.grid(row=0, column=1, padx=10, pady=6)
        ttk.Button(g1, text="Gravar Hostname", command=lambda: self._executar_snmp_set('1.3.6.1.2.1.1.5.0', e_name.get(), "sysName"), style="Acao.TButton").grid(row=0, column=2, pady=6)

        ttk.Label(g1, text="Localização Fís. (sysLocation):").grid(row=1, column=0, sticky="w", pady=6)
        e_loc = ttk.Entry(g1, width=32); e_loc.insert(0, "TI - Bancada")
        e_loc.grid(row=1, column=1, padx=10, pady=6)
        ttk.Button(g1, text="Gravar Local", command=lambda: self._executar_snmp_set('1.3.6.1.2.1.1.6.0', e_loc.get(), "sysLocation"), style="Acao.TButton").grid(row=1, column=2, pady=6)

    # ==========================================
    # ABA 4: DICIONÁRIO E DOCUMENTAÇÃO
    # ==========================================
    def _aba_dicionario_completo(self):
        f = self._criar_aba_rolavel(" 📚 Dicionário & Comandos ")
        g1 = tk.LabelFrame(f, text=" Guia Técnico e Documentação das Variáveis ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g1.pack(fill="both", expand=True, padx=10, pady=10)

        guia_texto = """GUIA COMPLETO DE COMANDOS PJL E VARIÁVEIS DA LEXMARK MX611:

1. VARIÁVEIS DE PAPEL E MÍDIA:
   - INTRAY1SIZE: Define o tamanho padrão do papel na gaveta (A4, LETTER, LEGAL).
   - LTRAY1PAPERTYPE: Define o tipo de suporte físico (PLAIN=Normal, CARDSTOCK=Papel Cartão, LABELS=Etiquetas).
   - DUPLEX: Ativa ou desativa a impressão frente e verso automática (ON / OFF).

2. AJUSTES FINOS DE FUSÃO:
   - LBONDWEIGHT / LCARDSTOCKWEIGHT: Define a gramatura (LIGHT, NORMAL, HEAVY) para controle térmico do fusor.
   - LCARDSTOCKTEXTURE: Define a textura superficial (SMOOTH, NORMAL, ROUGH) para aderência do toner.

3. COMANDOS DE DIAGNÓSTICO (Família INFO):
   - INFO STATUS: Retorna o estado mecânico instantâneo (portas abertas, erros, ocupada).
   - INFO VARIABLES: Despeja o dicionário completo de variáveis da NVRAM.
   - INFO CONFIG: Mostra hardware instalado, memória, versão de firmware e número de série."""

        lbl = tk.Label(g1, text=guia_texto, bg=self.COR_PAINEL, fg=self.COR_TEXTO, justify="left", font=("Consolas", 9))
        lbl.pack(anchor="w", fill="both", expand=True)

        ttk.Button(g1, text="📄 EXTRAIR DUMP COMPLETO DA PLACA (@PJL INFO VARIABLES)", command=lambda: self._enviar_pjl(['INFO VARIABLES'], 'Extrair Dicionário NVRAM'), style="Acao.TButton").pack(fill="x", pady=(15, 0))

    # ==========================================
    # ABA 5: TERMINAL LIVRE
    # ==========================================
    def _aba_terminal_livre(self):
        f = self._criar_aba_rolavel(" ⚙️ Terminal Livre ")
        g1 = tk.LabelFrame(f, text=" Caixa de Injeção Customizável (Porta 9100) ", bg=self.COR_PAINEL, fg=self.COR_TEXTO, padx=15, pady=15)
        g1.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(g1, text="Digite qualquer comando PJL customizado:", bg=self.COR_PAINEL, fg=self.COR_TEXTO_SECUNDARIO).pack(anchor="w", pady=(0, 8))

        e_livre = ttk.Entry(g1, width=50, font=("Consolas", 11)); e_livre.insert(0, "INFO STATUS")
        e_livre.pack(side="top", fill="x", pady=(0, 10))
        ttk.Button(g1, text="⚡ DISPARAR COMANDO CUSTOMIZADO", command=lambda: self._enviar_pjl([e_livre.get()], "Comando Customizado"), style="Acao.TButton").pack(side="top", fill="x", pady=(0, 15))

        ttk.Button(g1, text="🔄 REINICIAR PLACA LÓGICA (Reset Geral)", command=lambda: self._enviar_pjl(['RESET'], 'Reiniciar Sistema Lexmark'), style="Alerta.TButton").pack(side="bottom", fill="x", pady=4)

if __name__ == "__main__":
    app = TerminalTIWindow()
    app.mainloop()