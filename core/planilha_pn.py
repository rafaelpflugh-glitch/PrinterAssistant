"""
============================================================
PRINTER ASSISTANT
INTEGRAÇÃO COM A BASE DE DADOS DO GESTOR CPA (REDE W:)
============================================================

Responsabilidades:
    - Ler (sempre em modo somente leitura) a base oficial de
      Part Numbers compartilhada na rede W: pelo CPA Gestor;
    - Suportar tanto o JSON nativo (dados/base_cpa.json) quanto
      a planilha Excel (Base_de_Dados_Part_Numbers_Profissional.xlsx),
      priorizando automaticamente o arquivo mais recente;
    - Recarregar automaticamente o cache em memória quando o arquivo
      na rede for atualizado (sem precisar reiniciar o programa);
    - Fornecer busca inteligente de Part Number por modelo, tipo
      de consumível e fabricante, com fallback seguro para as
      tabelas internas caso a rede esteja indisponível.

IMPORTANTE:
    Este módulo NUNCA grava nem altera arquivos na pasta do Gestor.
============================================================
"""

from __future__ import annotations

import io
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CAMINHO_BASE_PADRAO = r"W:\TEC\Banco de Dados_Gestor de Part Number"
ARQUIVO_JSON_RELATIVO = os.path.join("dados", "base_cpa.json")
ARQUIVO_XLSX_PADRAO = "Base_de_Dados_Part_Numbers_Profissional.xlsx"

# Cache em memória para evitar leituras repetidas na rede
_CACHE: Dict[str, Any] = {
    "caminho_resolvido": None,
    "mtime": None,
    "itens": [],
    "origem": None,
}

# Famílias de modelos Lexmark que compartilham unidade de imagem / toner
_FAMILIAS_LEXMARK = {
    "50F": {"MS310", "MS410", "MS510", "MS610", "MX310", "MX410", "MX510", "MX511", "MX610", "MX611"},
    "56F": {"MS321", "MS421", "MS521", "MS621", "MS622", "MX321", "MX421", "MX521", "MX522", "MX622"},
    "52D": {"MS810", "MS811", "MS812", "MX710", "MX711", "MX810", "MX811", "MX812"},
    "58D": {"MS725", "MS821", "MS822", "MS823", "MS824", "MS825", "MS826", "MX721", "MX722", "MX725", "MX822", "MX824", "MX826"},
    "74C": {"CS720", "CS725", "CX725"},
}

# Padrões que identificam inequivocamente uma Unidade de Imagem pelo PN/Código Original
_REGEX_PN_IU = re.compile(r"(?:0Z00|0ZV0|DR-?\d|DRMS|2114-MX|2380-MX|2402-MX|227808|228237|E260X22G)", re.IGNORECASE)


def obter_caminho_base_configurado() -> str:
    """Lê o caminho da base do Gestor a partir de config.json (ou usa o padrão W:)."""
    try:
        from core.config import carregar_config
        cfg = carregar_config()
        caminho = str(cfg.get("caminho_base_pn") or "").strip()
        if caminho:
            return caminho
    except Exception:
        pass
    return CAMINHO_BASE_PADRAO


def _resolver_arquivos_candidatos(caminho_config: str) -> List[Tuple[str, str, float]]:
    """
    Retorna lista de tuplas (tipo, caminho_completo, mtime) ordenada do
    arquivo mais recente para o mais antigo.
    """
    candidatos: List[Tuple[str, str, float]] = []
    if not caminho_config:
        return candidatos

    p = Path(caminho_config)
    try:
        if not p.exists():
            return candidatos
    except OSError:
        return candidatos

    if p.is_file():
        ext = p.suffix.lower()
        tipo = "json" if ext == ".json" else "xlsx"
        try:
            candidatos.append((tipo, str(p), p.stat().st_mtime))
        except OSError:
            pass
        return candidatos

    # Se for pasta, verifica dados/base_cpa.json e a planilha .xlsx
    json_path = p / ARQUIVO_JSON_RELATIVO
    try:
        if json_path.is_file():
            candidatos.append(("json", str(json_path), json_path.stat().st_mtime))
    except OSError:
        pass

    xlsx_path = p / ARQUIVO_XLSX_PADRAO
    try:
        if xlsx_path.is_file():
            candidatos.append(("xlsx", str(xlsx_path), xlsx_path.stat().st_mtime))
        else:
            # Procura qualquer .xlsx válido na pasta caso o nome mude
            for item in p.iterdir():
                if item.is_file() and item.suffix.lower() == ".xlsx" and not item.name.startswith("~$"):
                    candidatos.append(("xlsx", str(item), item.stat().st_mtime))
                    break
    except OSError:
        pass

    # Prioriza o arquivo mais recentemente atualizado
    candidatos.sort(key=lambda x: x[2], reverse=True)
    return candidatos


def _ler_json_somente_leitura(caminho: str) -> List[Dict[str, str]]:
    with open(caminho, "r", encoding="utf-8") as f:
        bruto = json.load(f)

    lista_bruta = bruto.get("itens", []) if isinstance(bruto, dict) else (bruto if isinstance(bruto, list) else [])
    itens: List[Dict[str, str]] = []
    for row in lista_bruta:
        if not isinstance(row, dict):
            continue
        pn = str(row.get("part_number") or "").strip()
        if not pn or pn == "-":
            continue
        itens.append({
            "categoria": str(row.get("categoria") or "").strip(),
            "fornecedor": str(row.get("fornecedor") or "").strip(),
            "codigo_original": str(row.get("codigo_original") or "").strip(),
            "descricao_embalagem": str(row.get("descricao_embalagem") or "").strip(),
            "part_number": pn,
            "maquinas_compativeis": str(row.get("maquinas_compativeis") or "").strip(),
        })
    return itens


def _ler_xlsx_somente_leitura(caminho: str) -> List[Dict[str, str]]:
    import openpyxl

    # Copia os bytes para memória para nunca manter lock no arquivo da rede
    with open(caminho, "rb") as f:
        conteudo = io.BytesIO(f.read())

    wb = openpyxl.load_workbook(conteudo, data_only=True, read_only=True)
    try:
        ws = wb["Part Numbers & Suprimentos"] if "Part Numbers & Suprimentos" in wb.sheetnames else wb.active
        itens: List[Dict[str, str]] = []
        cabecalho_idx = None

        for idx, row in enumerate(ws.iter_rows(values_only=True), 1):
            if not row or all(v is None for v in row):
                continue
            primeira = str(row[0] or "").strip().lower()
            if cabecalho_idx is None:
                if "categoria" in primeira:
                    cabecalho_idx = idx
                continue

            vals = [str(v).strip() if v is not None else "" for v in row]
            while len(vals) < 6:
                vals.append("")

            pn = vals[4]
            if not pn or pn == "-":
                continue

            itens.append({
                "categoria": vals[0],
                "fornecedor": vals[1],
                "codigo_original": vals[2],
                "descricao_embalagem": vals[3],
                "part_number": pn,
                "maquinas_compativeis": vals[5],
            })
        return itens
    finally:
        wb.close()


def carregar_base_pn(caminho_override: Optional[str] = None, forcar_recarga: bool = False) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """
    Carrega os itens da base oficial do Gestor (somente leitura) com cache por mtime.
    Retorna (lista_itens, caminho_usado). Se indisponível, retorna ([], None).
    """
    caminho_cfg = caminho_override or obter_caminho_base_configurado()
    candidatos = _resolver_arquivos_candidatos(caminho_cfg)

    if not candidatos:
        return [], None

    for tipo, arq_path, mtime in candidatos:
        if (
            not forcar_recarga
            and _CACHE["caminho_resolvido"] == arq_path
            and _CACHE["mtime"] == mtime
            and _CACHE["itens"]
        ):
            return _CACHE["itens"], arq_path

        try:
            if tipo == "json":
                itens = _ler_json_somente_leitura(arq_path)
            else:
                itens = _ler_xlsx_somente_leitura(arq_path)

            if itens:
                _CACHE["caminho_resolvido"] = arq_path
                _CACHE["mtime"] = mtime
                _CACHE["itens"] = itens
                _CACHE["origem"] = tipo
                return itens, arq_path
        except Exception:
            continue

    return [], None


def status_base_pn(caminho_override: Optional[str] = None) -> Dict[str, Any]:
    """Retorna um resumo simples do status da conexão com a base da rede."""
    itens, origem = carregar_base_pn(caminho_override=caminho_override)
    return {
        "conectado": bool(itens and origem),
        "total_itens": len(itens),
        "arquivo": origem or "",
        "caminho_configurado": caminho_override or obter_caminho_base_configurado(),
    }


# ============================================================
# NORMALIZAÇÃO E EXPANSÃO DE MODELOS COMPATÍVEIS
# ============================================================

def _extrair_identificadores_modelo(modelo: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    De 'Lexmark MX611dhe' -> (modelo_base='MX611', prefixo='MX', numero='611')
    De 'Canon iR1643i'    -> (modelo_base='IR1643', prefixo='IR', numero='1643')
    """
    txt = str(modelo or "").upper().strip()
    m = re.search(r"\b(MS|MX|CS|CX|IR|MF|LBP|E|T|X|C|M|B)\s*-?\s*(\d{3,4})\b", txt)
    if m:
        pref, num = m.group(1), m.group(2)
        return f"{pref}{num}", pref, num

    m2 = re.search(r"(MS|MX|CS|CX|IR)(\d{3,4})", txt)
    if m2:
        pref, num = m2.group(1), m2.group(2)
        return f"{pref}{num}", pref, num

    m_num = re.search(r"\b(\d{3,4})\b", txt)
    if m_num:
        return None, None, m_num.group(1)

    return None, None, None


def _expandir_maquinas_compativeis(texto: str) -> Tuple[set, set]:
    """
    Expande strings da planilha como:
      - 'MS/MX511/610/611'      -> {'MS511','MX511','MS610','MX610','MS611','MX611'}, {'511','610','611'}
      - 'MS-MX321/421/522/622'  -> {'MS321','MX321',...}, {'321','421','522','622'}
      - 'MS725/821/MX721/722'   -> {'MS725','MS821','MX721','MX722'}, {'725','821','721','722'}
      - '1643'                  -> set(), {'1643'}
    """
    modelos_exatos = set()
    numeros = set()

    if not texto or texto.strip() == "-":
        return modelos_exatos, numeros

    txt = str(texto).upper()
    # Normaliza 'MS-MX321' -> 'MS/MX321' e separa por / , ; espaço
    txt = re.sub(r"\b(MS|MX|CS|CX)-(MS|MX|CS|CX)", r"\1/\2", txt)
    partes = [p.strip() for p in re.split(r"[/,;\s]+", txt) if p.strip()]

    prefixos_ativos: List[str] = []

    for parte in partes:
        # Prefixo puro (ex: 'MS' antes de '/MX511')
        if parte in ("MS", "MX", "CS", "CX", "IR", "MF", "LBP"):
            if parte not in prefixos_ativos:
                prefixos_ativos.append(parte)
            continue

        # Prefixo + número (ex: 'MX511DHE', 'MS725', 'IR1643I', 'DRE260')
        m_full = re.match(r"^(?:DR)?(MS|MX|CS|CX|IR|MF|LBP|E|T|X|C|M|B)(\d{3,4})", parte)
        if m_full:
            pref, num = m_full.group(1), m_full.group(2)
            numeros.add(num)
            # Se havia prefixos combinados pendentes (ex: MS/MX511), aplica todos
            if len(prefixos_ativos) >= 1 and pref not in prefixos_ativos and all(p in ("MS", "MX", "CS", "CX") for p in prefixos_ativos) and pref in ("MS", "MX", "CS", "CX"):
                prefixos_ativos.append(pref)
                for p_ativo in prefixos_ativos:
                    modelos_exatos.add(f"{p_ativo}{num}")
            else:
                prefixos_ativos = [pref]
                modelos_exatos.add(f"{pref}{num}")
            continue

        # Número puro (ex: '611', '611DHE', '1643')
        m_num = re.match(r"^(\d{3,4})", parte)
        if m_num:
            num = m_num.group(1)
            numeros.add(num)
            for p_ativo in prefixos_ativos:
                modelos_exatos.add(f"{p_ativo}{num}")
            continue

    return modelos_exatos, numeros


def _identificar_familia(modelo_base: Optional[str]) -> Optional[str]:
    if not modelo_base:
        return None
    for fam, membros in _FAMILIAS_LEXMARK.items():
        if modelo_base in membros:
            return fam
    return None


def _item_eh_unidade_imagem(item: Dict[str, str]) -> bool:
    cat = item["categoria"].lower()
    if any(k in cat for k in ("unidade", "imagem", "fotocondutor", "drum", "imaging")):
        return True
    # Corrige casos em que uma unidade (ex: 58D0Z00-INOVA) foi cadastrada sob Toners
    if _REGEX_PN_IU.search(item["part_number"]) or _REGEX_PN_IU.search(item["codigo_original"]):
        return True
    return False


def _item_eh_toner(item: Dict[str, str]) -> bool:
    if _item_eh_unidade_imagem(item):
        return False
    cat = item["categoria"].lower()
    return any(k in cat for k in ("toner", "cartucho"))


def _limpar_pn_etiqueta(pn: str) -> str:
    """
    Limpa o Part Number para caber perfeitamente no código de barras Code 128
    da etiqueta de produção (50x38mm). Se houver múltiplos PNs separados por '/',
    utiliza o primeiro código principal.
    """
    pn_limpo = str(pn or "").strip()
    if "/" in pn_limpo:
        pn_limpo = pn_limpo.split("/")[0].strip()
    return pn_limpo


def buscar_part_number_na_base(
    modelo: str,
    tipo: str,
    fabricante: str,
    caminho_override: Optional[str] = None,
) -> Optional[str]:
    """
    Busca o Part Number na base unificada da rede W: (Gestor CPA).
    Retorna o Part Number encontrado ou None (para acionar o fallback seguro).
    """
    itens, _ = carregar_base_pn(caminho_override=caminho_override)
    if not itens:
        return None

    quer_toner = "toner" in str(tipo).lower() or "cartucho" in str(tipo).lower()
    modelo_base, prefixo, numero = _extrair_identificadores_modelo(modelo)
    familia = _identificar_familia(modelo_base)

    fab_raw = str(fabricante or "").strip().upper()
    if not fab_raw:
        return None

    # Para REM, tenta primeiro um cadastro explícito REM; se não houver,
    # busca o código original OEM (Canon ou Lexmark) para manter 'REM - <PN>'.
    fornecedores_alvo: List[str] = [fab_raw]
    if "REM" in fab_raw:
        eh_canon = "CANON" in str(modelo or "").upper() or prefixo == "IR"
        fornecedores_alvo.append("CANON" if eh_canon else "LEXMARK")

    for forn_alvo in fornecedores_alvo:
        melhor_pn: Optional[str] = None
        melhor_score = 0

        for item in itens:
            forn_item = item["fornecedor"].strip().upper()
            if forn_item != forn_alvo:
                continue

            # Filtra categoria (toner vs unidade de imagem)
            if quer_toner:
                if not _item_eh_toner(item):
                    continue
            else:
                if not _item_eh_unidade_imagem(item):
                    continue

            score = 0
            modelos_comp, nums_comp = _expandir_maquinas_compativeis(item["maquinas_compativeis"])
            texto_aux = f"{item['part_number']} {item['codigo_original']} {item['descricao_embalagem']}".upper()

            # 1. Match exato de modelo completo (ex: MX611 em MX511/611)
            if modelo_base and modelo_base in modelos_comp:
                score += 120
            # 2. Match de modelo no próprio PN/descrição (ex: '2114-MX611' ou 'SM10001-20.5KIR1643')
            elif modelo_base and modelo_base in texto_aux:
                score += 100
            # 3. Match de número de modelo em maquinas_compativeis sem conflito de prefixo
            elif numero and numero in nums_comp:
                # Só aceita se não houver prefixo incompatível explícito (ex: MS610 vs MX610)
                conflito_prefixo = bool(
                    prefixo
                    and modelos_comp
                    and not any(m.startswith(prefixo) for m in modelos_comp)
                )
                if not conflito_prefixo:
                    score += 85
            # 4. Match por família Lexmark (ex: 50F0Z00 -> MX611 mesmo se a linha listou MX310/410/510/610)
            elif familia and (
                familia in texto_aux
                or any(m in _FAMILIAS_LEXMARK[familia] for m in modelos_comp)
            ):
                # Evita cruzar MS com MX quando há item específico para o prefixo
                if prefixo and modelos_comp and any(m.startswith(prefixo) for m in modelos_comp):
                    score += 65
                else:
                    score += 50

            # Caso especial Canon T06 / iR1643 sem maquinas_compativeis preenchida
            if score == 0 and (prefixo == "IR" and numero == "1643"):
                if "T06" in texto_aux or "3526C001" in texto_aux or "1643" in texto_aux:
                    score += 95

            if score <= 0:
                continue

            # Desempate: prefere categoria exata cadastrada (evita item mal categorizado)
            cat_lower = item["categoria"].lower()
            if (quer_toner and "toner" in cat_lower) or ((not quer_toner) and "unidade" in cat_lower):
                score += 10

            # Desempate de cor para coloridas (CS/CX): prioriza cor pedida ou BLACK por padrão
            if quer_toner:
                tipo_low = str(tipo or "").lower()
                if any(c in tipo_low for c in ("cyan", "ciano")):
                    if "CYAN" in texto_aux or "-CY" in texto_aux:
                        score += 15
                elif "magenta" in tipo_low:
                    if "MAGENTA" in texto_aux or "-MA" in texto_aux:
                        score += 15
                elif any(c in tipo_low for c in ("yellow", "amarelo")):
                    if "YELLOW" in texto_aux or "-YE" in texto_aux:
                        score += 15
                else:
                    if "BLACK" in texto_aux or "-BK" in texto_aux or "PRETO" in texto_aux or "HK0" in texto_aux:
                        score += 12
                    elif any(c in texto_aux for c in ("CYAN", "MAGENTA", "YELLOW", "-CY", "-MA", "-YE")):
                        score -= 10

            # Desempate: para toners Lexmark, prioriza códigos de maior rendimento (U / X)
            if quer_toner and any(k in item["part_number"].upper() for k in ("U00", "U0E", "X00", "504U", "604X", "227192", "2608")):
                score += 5

            if score > melhor_score:
                melhor_score = score
                melhor_pn = _limpar_pn_etiqueta(item["part_number"])

        if melhor_pn:
            return melhor_pn

    return None
