"""
============================================================
PRINTER ASSISTANT
RELATÓRIO DE PRODUÇÃO (ETIQUETA DE CONSUMÍVEIS - 50x38mm)
============================================================

Responsabilidades:

    - Gerar etiquetas de produção de consumíveis (Unidades de Imagem/Toner);
    - Mapear automaticamente o Part Number por modelo (Unidade de Imagem ou Toner);
    - Diferenciar fabricante (Lexmark, REM, GLOBAL) e buscar o código da planilha;
    - Imprimir em rolo de 2 carreiras (duas etiquetas lado a lado) na horizontal;
    - Formatar códigos de barras compactos e centralizados no printable area;
    - Margens simétricas nas duas etiquetas (X=45 na esquerda e X=465 na direita);
    - Ajustar densidade térmica (DENSITY 14) e alinhamento do GAP;
    - Enviar caractere EOT (\x04) e fechar socket TCP para liberar visor da impressora;
    - Enviar o código TSPL para a etiquetadora de Produção configurada.

============================================================
"""

import re
import socket
from typing import Any, Dict, Optional

try:
    from core.config import resolver_ip
except ImportError:
    def resolver_ip(ip, tipo="producao"):
        return ip


# ============================================================
# CONFIGURAÇÃO DE REDE PADRÃO
# ============================================================

PRODUCAO_IP_PADRAO = "192.168.14.111"
PRODUCAO_PORTA_PADRAO = 9100

TSC_IP = PRODUCAO_IP_PADRAO
TSC_PORTA = PRODUCAO_PORTA_PADRAO


# ============================================================
# TABELAS DE PART NUMBERS (EXTRAÍDAS DA PLANILHA PROFISSIONAL)
# ============================================================

MAPA_PN_LEXMARK = {
    # Família 50F (310 a 611)
    "MS310": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MS410": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MS510": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MS610": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MX310": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MX410": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MX510": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MX511": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MX610": {"iu": "50F0Z00", "toner": "50F4X00"},
    "MX611": {"iu": "50F0Z00", "toner": "50F4X00"},

    # Família 56F (321 a 622)
    "MS321": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MS421": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MS521": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MS621": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MS622": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MX321": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MX421": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MX521": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MX522": {"iu": "56F0Z00", "toner": "56FBU00"},
    "MX622": {"iu": "56F0Z00", "toner": "56FBU00"},

    # Família 52D (710 a 812)
    "MS810": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MS811": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MS812": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MX710": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MX711": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MX810": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MX811": {"iu": "52D0Z00", "toner": "52D4X00"},
    "MX812": {"iu": "52D0Z00", "toner": "52D4X00"},

    # Família 58D (721 a 826)
    "MS821": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MS822": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MS823": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MS825": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MS826": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MX721": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MX722": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MX822": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MX824": {"iu": "58D0Z00", "toner": "58DBU0E"},
    "MX826": {"iu": "58D0Z00", "toner": "58DBU0E"},
    
    # Família Colorida CS/CX (CS720, CS725, CX725)
    "CS720": {"iu": "74C0ZV0", "toner": "74C40K0"},
    "CS725": {"iu": "74C0ZV0", "toner": "74C40K0"},
    "CX725": {"iu": "74C0ZV0", "toner": "74C40K0"},
}

MAPA_PN_GLOBAL = {
    # Família 50F (310 a 611)
    "MS310": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MS410": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MS510": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MS610": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MX310": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MX410": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MX511": {"iu": "2114-MX611", "toner": "1041-504U"},
    "MX611": {"iu": "2114-MX611", "toner": "1041-504U"},

    # Família 56F (321 a 622)
    "MS321": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MS421": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MS521": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MS621": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MS622": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MX321": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MX421": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MX521": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MX522": {"iu": "2402-MX622", "toner": "2571-MS621"},
    "MX622": {"iu": "2402-MX622", "toner": "2571-MS621"},

    # Família 52D (710 a 812)
    "MS810": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MS811": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MS812": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MX710": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MX711": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MX810": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MX811": {"iu": "2380-MX711", "toner": "1054-524-624X"},
    "MX812": {"iu": "2380-MX711", "toner": "1054-524-624X"},

    # Família 58D (721 a 826)
    "MS821": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MS822": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MS823": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MS825": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MS826": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MX721": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MX722": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MX822": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MX824": {"iu": "58D0Z00", "toner": "2608-MX722"},
    "MX826": {"iu": "58D0Z00", "toner": "2608-MX722"},
}


MAPA_PN_3I = {
    "MS310": {"iu": "227808", "toner": "50F4X00-INOVA"},
    "MS410": {"iu": "227808", "toner": "50F4X00-INOVA"},
    "MS510": {"iu": "227808", "toner": "50F4X00-INOVA"},
    "MS610": {"iu": "227808", "toner": "50F4X00-INOVA"},
    "MX310": {"iu": "227808", "toner": "227192"},
    "MX410": {"iu": "227808", "toner": "227192"},
    "MX510": {"iu": "227808", "toner": "227192"},
    "MX511": {"iu": "227808", "toner": "227192"},
    "MX610": {"iu": "227808", "toner": "227192"},
    "MX611": {"iu": "227808", "toner": "227192"},
    "MX710": {"iu": "228237", "toner": "52D4X00-INOVA"},
    "MX711": {"iu": "228237", "toner": "52D4X00-INOVA"},
    "MX810": {"iu": "228237", "toner": "52D4X00-INOVA"},
    "MX811": {"iu": "228237", "toner": "52D4X00-INOVA"},
    "MX812": {"iu": "228237", "toner": "52D4X00-INOVA"},
}

MAPA_PN_VRI = {
    "MS310": {"iu": "50F0Z00", "toner": "9253-50FBX00"},
    "MS410": {"iu": "50F0Z00", "toner": "9253-50FBX00"},
    "MS510": {"iu": "50F0Z00", "toner": "9253-50FBX00"},
    "MS610": {"iu": "50F0Z00", "toner": "9253-50FBX00"},
    "MX310": {"iu": "50F0Z00", "toner": "60F4X00-VRI"},
    "MX410": {"iu": "50F0Z00", "toner": "60F4X00-VRI"},
    "MX510": {"iu": "50F0Z00", "toner": "60F4X00-VRI"},
    "MX511": {"iu": "50F0Z00", "toner": "60F4X00-VRI"},
    "MX610": {"iu": "50F0Z00", "toner": "60F4X00-VRI"},
    "MX611": {"iu": "50F0Z00", "toner": "60F4X00-VRI"},
    "MS621": {"iu": "56F0Z00", "toner": "56F4U00-25K-VRI"},
    "MS622": {"iu": "56F0Z00", "toner": "56F4U00-25K-VRI"},
    "MX622": {"iu": "56F0Z00", "toner": "56F4U00-25K-VRI"},
    "MS810": {"iu": "DRMS810-VRI", "toner": "52DBX00-524X-VRI"},
    "MS811": {"iu": "DRMS810-VRI", "toner": "52DBX00-524X-VRI"},
    "MS812": {"iu": "DRMS810-VRI", "toner": "52DBX00-524X-VRI"},
    "MX710": {"iu": "DRMS810-VRI", "toner": "52DBX00-524X-VRI"},
    "MX711": {"iu": "DRMS810-VRI", "toner": "52DBX00-524X-VRI"},
}


class ProducaoError(Exception):
    """Erro controlado na geração ou impressão da etiqueta de produção."""
    pass


# ============================================================
# OBTER PART NUMBER
# ============================================================

def obter_part_number(modelo: str, tipo: str, fabricante: str) -> str:
    """
    Retorna o Part Number correspondente ao modelo, tipo e fabricante.
    """
    categoria = "toner" if "toner" in str(tipo).lower() or "cartucho" in str(tipo).lower() else "iu"
    
    if not modelo or str(modelo).strip().lower() in ("desconhecido", "none", ""):
        modelo = "MX611"
        
    modelo_limpo = str(modelo).upper()
    fabricante_limpo = str(fabricante).upper().strip()

    # Define qual mapa e fallbacks usar
    if "GLOBAL" in fabricante_limpo:
        mapa = MAPA_PN_GLOBAL
        pn_padrao_50f = "1041-504U" if categoria == "toner" else "2114-MX611"
        pn_padrao_56f = "2571-MS621" if categoria == "toner" else "2402-MX622"
        pn_padrao_52d = "1054-524-624X" if categoria == "toner" else "2380-MX711"
        pn_padrao_58d = "2608-MX722" if categoria == "toner" else "58D0Z00"
    elif "3I" in fabricante_limpo:
        mapa = MAPA_PN_3I
        pn_padrao_50f = "227192" if categoria == "toner" else "227808"
        pn_padrao_56f = "56FBU00" if categoria == "toner" else "56F0Z00"
        pn_padrao_52d = "52D4X00-INOVA" if categoria == "toner" else "228237"
        pn_padrao_58d = "58DBU0E" if categoria == "toner" else "58D0Z00"
    elif "VRI" in fabricante_limpo:
        mapa = MAPA_PN_VRI
        pn_padrao_50f = "60F4X00-VRI" if categoria == "toner" else "50F0Z00"
        pn_padrao_56f = "56F4U00-25K-VRI" if categoria == "toner" else "56F0Z00"
        pn_padrao_52d = "52DBX00-524X-VRI" if categoria == "toner" else "DRMS810-VRI"
        pn_padrao_58d = "58DBU0E" if categoria == "toner" else "58D0Z00"
    else:
        mapa = MAPA_PN_LEXMARK
        pn_padrao_50f = "50F4X00" if categoria == "toner" else "50F0Z00"
        pn_padrao_56f = "56FBU00" if categoria == "toner" else "56F0Z00"
        pn_padrao_52d = "52D4X00" if categoria == "toner" else "52D0Z00"
        pn_padrao_58d = "58DBU0E" if categoria == "toner" else "58D0Z00"

    # Busca específica pelo modelo
    for chave, pns in mapa.items():
        if chave in modelo_limpo:
            return pns[categoria]

    # Busca genérica por substring de família se não houver exato
    if any(m in modelo_limpo for m in ["310", "410", "510", "511", "610", "611"]):
        return pn_padrao_50f

    if any(m in modelo_limpo for m in ["321", "421", "521", "522", "621", "622"]):
        return pn_padrao_56f

    if any(m in modelo_limpo for m in ["710", "711", "810", "811", "812"]):
        return pn_padrao_52d

    if any(m in modelo_limpo for m in ["721", "722", "725", "821", "822", "823", "824", "825", "826"]):
        return pn_padrao_58d

    # Fallback final de segurança
    return pn_padrao_50f


# ============================================================
# GERAR TSPL AJUSTADO (MARGENS SIMÉTRICAS X=45 E X=465)
# ============================================================

def gerar_tspl_producao(texto_pn: str, serial: str) -> str:
    """
    Gera o código TSPL para rolo de 2 colunas (104mm total x 38mm altura):
    - Coluna Esquerda: X = 45 (Margem perfeitamente alinhada com a direita)
    - Coluna Direita: X = 465 (Margem direita ajustada)
    - DENSITY 14 & SPEED 3: Nitidez e fusão térmica perfeitas
    - GAP 3 mm,0 mm & OFFSET 0 mm & REFERENCE 0,0 & SHIFT 0: Parada exata no salto sem descalibrar o sensor da TSC
    """
    texto_pn = str(texto_pn).strip().replace('"', "'")
    serial = str(serial).strip().replace('"', "'")

    linhas = [
        "SIZE 104 mm,38 mm",  # Largura total física das 2 carreiras
        "GAP 3 mm,0 mm",      # Distância real de GAP entre etiquetas
        "OFFSET 0 mm",        # Zerar deslocamento de parada
        "REFERENCE 0,0",      # Origem de coordenadas zerada
        "SHIFT 0",            # Sem deslocamento vertical extra
        "DENSITY 14",         # Intensidade alta do preto (0 a 15)
        "SPEED 3",            # Velocidade ajustada de fusão térmica
        "DIRECTION 1",        # Orientação horizontal legível
        "SET TEAR ON",        # Habilita parada no picote/serrilha
        "CLS",

        # ----------------------------------------------------
        # ETIQUETA 1: COLUNA DA ESQUERDA (X = 45 - MARGEM ALINHADA)
        # ----------------------------------------------------
        # Bloco Superior: Part Number
        f'BARCODE 45,30,"128",40,2,0,2,2,"{texto_pn}"',
        # Bloco Inferior: Número de Série
        f'BARCODE 45,150,"128",40,2,0,2,2,"{serial}"',

        # ----------------------------------------------------
        # ETIQUETA 2: COLUNA DA DIREITA (X = 465 - MARGEM ALINHADA)
        # ----------------------------------------------------
        # Bloco Superior: Part Number
        f'BARCODE 465,30,"128",40,2,0,2,2,"{texto_pn}"',
        # Bloco Inferior: Número de Série
        f'BARCODE 465,150,"128",40,2,0,2,2,"{serial}"',

        "PRINT 1,1",
    ]

    return "\r\n".join(linhas) + "\r\n"


# ============================================================
# ALIAS DE COMPATIBILIDADE PARA A INTERFACE (gerar_tspl)
# ============================================================

def gerar_tspl(serial: Any = "", fabricante: str = "REM", tipo: str = "unidade_imagem", modelo: str = "MX611", *args, **kwargs) -> str:
    """
    Função de compatibilidade requisitada pela interface PrinterView.
    Aceita tanto argumentos nomeados/posicionais quanto um dicionário de dados.
    """
    if isinstance(serial, dict):
        dados_dict = serial
        serial = dados_dict.get("serial", "")
        fabricante = dados_dict.get("fabricante", fabricante)
        tipo = dados_dict.get("tipo", tipo)
        modelo = dados_dict.get("modelo") or dados_dict.get("modelo_maquina") or modelo

    device = kwargs.get("device")
    if device is not None and (not modelo or modelo in ("MS510", "MX611", "Desconhecido")):
        try:
            dados_dev = device.to_dict() if hasattr(device, "to_dict") else {}
            ident = dados_dev.get("identificacao", {}) or {}
            mod_dev = ident.get("modelo") or getattr(device, "modelo", None)
            if callable(mod_dev):
                mod_dev = mod_dev()
            if mod_dev and str(mod_dev).strip().lower() not in ("desconhecido", "none", ""):
                modelo = str(mod_dev).strip()
        except Exception:
            pass

    fabricante_limpo = str(fabricante).strip().upper()
    
    # Busca o PN considerando o Fabricante e Modelo corretos
    pn = obter_part_number(modelo, tipo, fabricante_limpo)

    if "REM" in fabricante_limpo:
        texto_pn = f"REM - {pn}"
    elif "GLOBAL" in fabricante_limpo:
        # Se for Global, imprime SÓ o código da Global (ex: 2114-MX611, 1041-504U)
        texto_pn = pn
    else:
        # LEXMARK / Original (ou 3I / VRI): imprime apenas o Part Number real do insumo
        texto_pn = pn

    return gerar_tspl_producao(texto_pn=texto_pn, serial=str(serial))


gerar_etiqueta = gerar_tspl


# ============================================================
# ENVIAR PARA IMPRESSORA TÉRMICA DE PRODUÇÃO (COM TCP FIN E EOT)
# ============================================================

def enviar_producao_raw(tspl_str: str, ip: str = PRODUCAO_IP_PADRAO, porta: int = PRODUCAO_PORTA_PADRAO) -> bool:
    """
    Envia o comando TSPL direto via TCP RAW.
    Adiciona o caractere de controle EOT (\x04) e encerra a conexão TCP via SHUT_WR
    para forçar a impressora a finalizar o job de impressão e limpar o status do visor.
    """
    ip_destino = resolver_ip(ip, tipo="producao")

    try:
        # Garante envio do sinal de fim de transmissão (EOT / End of Transmission)
        if not tspl_str.endswith("\x04"):
            tspl_str += "\x04"

        dados = tspl_str.encode("cp1252", errors="replace")
        with socket.create_connection((ip_destino, porta), timeout=10) as sock:
            sock.sendall(dados)
            try:
                sock.shutdown(socket.SHUT_WR)
            except Exception:
                pass
        return True
    except Exception as e:
        raise ProducaoError(
            f"Não foi possível enviar a etiqueta de Produção para {ip_destino}:{porta}.\n\n{e}"
        ) from e


# ============================================================
# ALIAS DE COMPATIBILIDADE PARA A IMPRESSÃO TSPL DIRETA
# ============================================================

def imprimir_tspl(tspl_dado: Any) -> bool:
    """
    Função de compatibilidade para imprimir comando TSPL direto.
    Aceita string TSPL ou dicionário contendo 'tspl' e opcionalmente 'ip'.
    """
    if isinstance(tspl_dado, dict):
        tspl_str = tspl_dado.get("tspl", "")
        ip_alvo = tspl_dado.get("ip", PRODUCAO_IP_PADRAO)
        porta_alvo = tspl_dado.get("porta", PRODUCAO_PORTA_PADRAO)
    else:
        tspl_str = str(tspl_dado)
        ip_alvo = PRODUCAO_IP_PADRAO
        porta_alvo = PRODUCAO_PORTA_PADRAO

    return enviar_producao_raw(tspl_str, ip=ip_alvo, porta=porta_alvo)


# ============================================================
# IMPRIMIR RELATÓRIO DE PRODUÇÃO
# ============================================================

def imprimir_relatorio_producao(device: Any, fabricante: str = "REM", tipo: str = "unidade_imagem") -> Dict[str, Any]:
    """
    Função principal chamada pela interface para a etiqueta de Produção.
    """
    if device is None:
        raise ProducaoError("Nenhum equipamento selecionado.")

    dados = device.to_dict() if hasattr(device, "to_dict") else {}
    identificacao = dados.get("identificacao", {})

    modelo = (
        identificacao.get("modelo")
        or getattr(device, "modelo", "")
        or "MS510"
    )

    supplies = dados.get("supplies", [])
    serial_unidade = ""

    # Busca estrita pelo serial específico do consumível correto (Toner ou Unidade de Imagem)
    termo_busca = "toner" if "toner" in str(tipo).lower() else "unidade_imagem"
    for item in supplies:
        tipo_item = str(item.get("tipo", "")).lower()
        nome_item = str(item.get("nome", "") or item.get("descricao", "")).lower()

        is_toner = "toner" in termo_busca and ("toner" in tipo_item or "toner" in nome_item)
        is_drum = "unidade_imagem" in termo_busca and any(t in tipo_item or t in nome_item for t in ["unidade", "image", "drum", "photoconductor", "imaging"])

        if is_toner or is_drum:
            serial_unidade = item.get("numero_serie") or item.get("serial") or item.get("cartridge_serial") or ""
            if serial_unidade and serial_unidade.lower() not in ["none", "desconhecido", "n/a", ""]:
                break

    # Se não encontrar o serial do consumível específico, impede puxar o serial da impressora por engano
    if not serial_unidade or serial_unidade.lower() in ["none", "desconhecido", "n/a", ""]:
        serial_unidade = "SN_INDISPONIVEL"

    tspl_comando = gerar_tspl(
        serial=serial_unidade,
        fabricante=fabricante,
        tipo=tipo,
        modelo=modelo
    )

    enviar_producao_raw(tspl_comando)
    
    # Extrair qual foi o PN gerado na etiqueta final
    fabricante_limpo = str(fabricante).strip().upper()
    pn_extraido = obter_part_number(modelo, tipo, fabricante_limpo)

    return {
        "sucesso": True,
        "relatorio": "producao",
        "fabricante": fabricante_limpo,
        "part_number": pn_extraido,
        "serial": serial_unidade,
        "ip_destino": resolver_ip(PRODUCAO_IP_PADRAO, tipo="producao"),
    }