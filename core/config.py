"""
============================================================
ASSISTENTE DE IMPRESSORAS - CONFIGURAÇÕES DO SISTEMA
============================================================
Gerencia as configurações de IPs padrão e exceções para
as etiquetadoras térmicas: Produção, RMA e Ativo Patrimonial.
============================================================
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

CONFIG_PADRAO = {
    # 1. Produção (Consumíveis 50x38mm)
    "producao_ip_padrao": "192.168.14.111",
    "producao_ip_excecao": "192.168.14.151",
    "producao_usar_excecao": True,  # Ativo por padrão se a .111 estiver desligada na bancada

    # 2. RMA / UST (Unidade de Imagem 100x150mm)
    "rma_ip_padrao": "192.168.14.151",
    "rma_ip_excecao": "192.168.14.151",
    "rma_usar_excecao": False,

    # 3. Ativo Patrimonial (100x150mm)
    "ativo_ip_padrao": "192.168.14.151",
    "ativo_ip_excecao": "192.168.14.151",
    "ativo_usar_excecao": False,

    # 4. Histórico de IPs manuais
    "ips_recentes": [],
}

def carregar_ips_recentes():
    """Retorna a lista de IPs inseridos manualmente recentemente."""
    config = carregar_config()
    recentes = config.get("ips_recentes", [])
    if isinstance(recentes, list):
        return [str(ip).strip() for ip in recentes if ip]
    return []

def salvar_ip_recente(ip):
    """Adiciona um IP ao topo do histórico de IPs recentes (sem duplicatas)."""
    if not ip or not isinstance(ip, str):
        return
    ip_limpo = ip.strip()
    if not ip_limpo:
        return
    config = carregar_config()
    recentes = config.get("ips_recentes", [])
    if not isinstance(recentes, list):
        recentes = []
    if ip_limpo in recentes:
        recentes.remove(ip_limpo)
    recentes.insert(0, ip_limpo)
    config["ips_recentes"] = recentes[:15]
    salvar_config(config)

def carregar_config():
    """Lê as configurações salvas do arquivo config.json."""
    if not CONFIG_FILE.exists():
        salvar_config(CONFIG_PADRAO)
        return CONFIG_PADRAO.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            config = CONFIG_PADRAO.copy()
            config.update(dados)
            return config
    except Exception as e:
        print(f"[CONFIG] Erro ao ler config.json: {e}")
        return CONFIG_PADRAO.copy()

def salvar_config(config):
    """Grava as alterações no arquivo config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[CONFIG] Erro ao salvar config.json: {e}")
        return False

def resolver_ip(ip_solicitado=None, tipo="producao"):
    """
    Retorna o IP efetivo a ser utilizado para o envio da impressão.
    
    Se a opção de EXCEÇÃO da categoria estiver marcada, retorna o IP de Exceção.
    Caso contrário, retorna o IP Padrão configurado.
    """
    config = carregar_config()
    tipo_limpo = str(tipo).lower().strip()

    # Roteamento 1: Produção / Consumíveis
    if tipo_limpo in ("producao", "consumiveis"):
        if config.get("producao_usar_excecao", False):
            return config.get("producao_ip_excecao") or "192.168.14.151"
        return config.get("producao_ip_padrao") or "192.168.14.111"

    # Roteamento 2: RMA / UST
    if tipo_limpo in ("rma", "ust_etiqueta"):
        if config.get("rma_usar_excecao", False):
            return config.get("rma_ip_excecao") or "192.168.14.151"
        return config.get("rma_ip_padrao") or "192.168.14.151"

    # Roteamento 3: Ativo Patrimonial
    if tipo_limpo in ("ativo", "patrimonio"):
        if config.get("ativo_usar_excecao", False):
            return config.get("ativo_ip_excecao") or "192.168.14.151"
        return config.get("ativo_ip_padrao") or "192.168.14.151"

    # Interceptação de segurança para código legado chamando o IP .111 diretamente
    if ip_solicitado == "192.168.14.111" and config.get("producao_usar_excecao", False):
        return config.get("producao_ip_excecao", "192.168.14.151")

    return ip_solicitado or config.get("producao_ip_padrao", "192.168.14.111")