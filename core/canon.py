"""
============================================================
PRINTER ASSISTANT
MÓDULO DE ENGENHARIA E DIAGNÓSTICO CANON (imageRUNNER / iR)
============================================================

Responsabilidades:
    - Identificação precisa de hardware Canon via SNMP e PJL;
    - Leitura da Canon Enterprise MIB (1.3.6.1.4.1.1602);
    - Leitura e mapeamento de contadores detalhados:
        Total, Impressão, Cópia, Scanner, Duplex;
    - Nível do cartucho de Toner (T06 / GPR / etc.);
    - Estimativa/Leitura do Tambor / Fotocondutor (Drum Unit);
    - Detecção de firmware e conectividade real (SNMP, Web RUI, PJL);
    - Arquitetura 100% isolada, sem interferir no motor Lexmark.

============================================================
"""

import asyncio
import re
import socket
from typing import Any, Dict, Optional, Tuple

from core.snmp import (
    SNMPPrinter,
    OID_SYS_DESCRICAO,
    OID_PRT_SERIAL,
    OID_PRT_PAGECOUNT,
)


# ============================================================
# OIDS ESPECÍFICOS CANON ENTERPRISE MIB (1.3.6.1.4.1.1602)
# ============================================================

OID_CANON_MODELO_CURTO = "1.3.6.1.4.1.1602.1.1.1.1.0"
OID_CANON_FIRMWARE     = "1.3.6.1.4.1.1602.1.1.1.4.0"
OID_CANON_SERIAL       = "1.3.6.1.4.1.1602.1.2.1.4.0"
OID_CANON_SERIAL_ALT   = "1.3.6.1.4.1.1602.1.2.1.8.1.3.1.1"

# Contadores Canônicos Canon (imageRUNNER / iR Series)
OID_CANON_CONT_TOTAL1  = "1.3.6.1.4.1.1602.1.11.1.4.1.4.101"
OID_CANON_CONT_DUPLEX  = "1.3.6.1.4.1.1602.1.11.1.4.1.4.114"
OID_CANON_CONT_COPIA   = "1.3.6.1.4.1.1602.1.11.1.4.1.4.201"
OID_CANON_CONT_PRINT   = "1.3.6.1.4.1.1602.1.11.1.4.1.4.301"
OID_CANON_CONT_SCAN    = "1.3.6.1.4.1.1602.1.11.1.4.1.4.501"
OID_CANON_CONT_FAX     = "1.3.6.1.4.1.1602.1.11.1.4.1.4.701"

# Suprimentos Printer-MIB
OID_PRT_SUPPLY1_DESC   = "1.3.6.1.2.1.43.11.1.1.6.1.1"
OID_PRT_SUPPLY1_MAX    = "1.3.6.1.2.1.43.11.1.1.8.1.1"
OID_PRT_SUPPLY1_LEVEL  = "1.3.6.1.2.1.43.11.1.1.9.1.1"

# Host Resources MIB (para nome comercial completo)
OID_HR_DEVICE_DESCR = "1.3.6.1.2.1.25.3.2.1.3.1"


class CanonCollector:
    """
    Coletor de diagnóstico e telemetria especializado para equipamentos Canon.
    """

    def __init__(self, ip: str, community: str = "public"):
        self.ip = ip
        self.community = community
        self.snmp = SNMPPrinter(ip, community)

    # --------------------------------------------------------
    # DETECÇÃO RÁPIDA: É UMA CANON?
    # --------------------------------------------------------
    async def eh_canon(self) -> bool:
        """Verifica se o dispositivo no IP é um equipamento Canon."""
        try:
            desc = await self.snmp.get(OID_SYS_DESCRICAO)
            if desc and "canon" in str(desc).lower():
                return True

            hr_desc = await self.snmp.get(OID_HR_DEVICE_DESCR)
            if hr_desc and "canon" in str(hr_desc).lower():
                return True

            canon_mod = await self.snmp.get(OID_CANON_MODELO_CURTO)
            if canon_mod:
                return True
        except Exception:
            pass
        return False

    # --------------------------------------------------------
    # TESTES DE CONECTIVIDADE
    # --------------------------------------------------------
    def testar_porta_tcp(self, porta: int, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((self.ip, porta), timeout=timeout):
                return True
        except Exception:
            return False

    def testar_pjl(self) -> Optional[str]:
        """Tenta consultar identificação via PJL na porta 9100."""
        try:
            with socket.create_connection((self.ip, 9100), timeout=1.5) as s:
                s.sendall(b"\x1b%-12345X@PJL\r\n@PJL INFO ID\r\n\x1b%-12345X")
                resp = s.recv(1024)
                m = re.search(r'@PJL\s+INFO\s+ID\s*[\r\n]+"([^"]+)"', resp.decode("ascii", errors="ignore"))
                if m:
                    return m.group(1).strip()
        except Exception:
            pass
        return None

    # --------------------------------------------------------
    # COLETA COMPLETA CANON
    # --------------------------------------------------------
    async def coletar(self) -> Dict[str, Any]:
        """
        Executa a coleta de engenharia completa na Canon:
        Identificação, Contadores detalhados e Suprimentos.
        """
        resultado = {
            "fabricante": "Canon",
            "modelo": "Canon imageRUNNER",
            "familia": "imageRUNNER",
            "tipo": "Multifuncional Laser Mono",
            "serial": "Desconhecido",
            "firmware": "Desconhecido",
            "contador": None,
            "contadores_detalhados": {},
            "supplies": [],
            "suprimentos": [],
            "conectividade": {
                "ip": self.ip,
                "pjl": False,
                "sysdebug": False,  # Canon não usa Sysdebug Lexmark
                "snmp": True,
                "web": False,
                "raw": False,
                "ipp": False,
            },
        }

        # 1. Testes de conectividade física
        porta_pjl = self.testar_porta_tcp(9100)
        resultado["conectividade"]["pjl"] = porta_pjl
        resultado["conectividade"]["raw"] = porta_pjl
        resultado["conectividade"]["web"] = self.testar_porta_tcp(80) or self.testar_porta_tcp(443)
        resultado["conectividade"]["ipp"] = self.testar_porta_tcp(631)

        # 2. Identificação de Modelo, Firmware, Serial, Contadores e Suprimentos
        # Executa consultas SNMP em paralelo para máxima velocidade
        (
            hr_desc,
            sys_desc,
            canon_mod_curto,
            serial_canon,
            serial_alt,
            serial_prt,
            fw,
            cont_principal,
            total1,
            print_val,
            copia_val,
            scan_val,
            duplex_val,
            fax_val,
            desc_toner,
            max_toner,
            lvl_toner,
        ) = await asyncio.gather(
            self.snmp.get(OID_HR_DEVICE_DESCR),
            self.snmp.get(OID_SYS_DESCRICAO),
            self.snmp.get(OID_CANON_MODELO_CURTO),
            self.snmp.get(OID_CANON_SERIAL),
            self.snmp.get(OID_CANON_SERIAL_ALT),
            self.snmp.get(OID_PRT_SERIAL),
            self.snmp.get(OID_CANON_FIRMWARE),
            self.snmp.get(OID_PRT_PAGECOUNT),
            self.snmp.get(OID_CANON_CONT_TOTAL1),
            self.snmp.get(OID_CANON_CONT_PRINT),
            self.snmp.get(OID_CANON_CONT_COPIA),
            self.snmp.get(OID_CANON_CONT_SCAN),
            self.snmp.get(OID_CANON_CONT_DUPLEX),
            self.snmp.get(OID_CANON_CONT_FAX),
            self.snmp.get(OID_PRT_SUPPLY1_DESC),
            self.snmp.get(OID_PRT_SUPPLY1_MAX),
            self.snmp.get(OID_PRT_SUPPLY1_LEVEL),
            return_exceptions=True,
        )

        pjl_id = self.testar_pjl() if porta_pjl else None

        # Helper para filtrar exceções de gather
        def _val(res):
            if isinstance(res, Exception):
                return None
            return res

        hr_desc = _val(hr_desc)
        sys_desc = _val(sys_desc)
        canon_mod_curto = _val(canon_mod_curto)
        fw = _val(fw)
        cont_principal = _val(cont_principal)
        total1 = _val(total1)
        print_val = _val(print_val)
        copia_val = _val(copia_val)
        scan_val = _val(scan_val)
        duplex_val = _val(duplex_val)
        fax_val = _val(fax_val)
        desc_toner = _val(desc_toner)
        max_toner = _val(max_toner)
        lvl_toner = _val(lvl_toner)

        # Normalização do Modelo
        modelo_candidato = None
        if hr_desc and "canon" in str(hr_desc).lower():
            modelo_candidato = str(hr_desc).strip()
        elif sys_desc and "canon" in str(sys_desc).lower():
            modelo_candidato = str(sys_desc).split("/")[0].strip()
        elif canon_mod_curto:
            modelo_candidato = f"Canon {canon_mod_curto}"
        elif pjl_id:
            modelo_candidato = f"Canon {pjl_id}"

        if modelo_candidato:
            if not modelo_candidato.lower().startswith("canon"):
                modelo_candidato = f"Canon {modelo_candidato}"
            resultado["modelo"] = modelo_candidato

        # Família e Tipo
        mod_upper = resultado["modelo"].upper()
        if "IR" in mod_upper or "IMAGERUNNER" in mod_upper:
            resultado["familia"] = "imageRUNNER"
            if " C" in mod_upper or "-C" in mod_upper or "COLOR" in mod_upper:
                resultado["tipo"] = "Multifuncional Laser Color"
            else:
                resultado["tipo"] = "Multifuncional Laser Mono"
        elif "IMAGECLASS" in mod_upper or "MF" in mod_upper:
            resultado["familia"] = "imageCLASS"
            resultado["tipo"] = "Multifuncional Laser"
        elif "LBP" in mod_upper:
            resultado["familia"] = "i-SENSYS / LBP"
            resultado["tipo"] = "Impressora Laser"

        # 3. Número de Série
        serial = _val(serial_canon) or _val(serial_alt) or _val(serial_prt)
        if serial:
            serial_limpo = str(serial).strip()
            serial_limpo = re.sub(r"-\d+-\d+$", "", serial_limpo)
            if not re.fullmatch(r"0+", serial_limpo):
                resultado["serial"] = serial_limpo

        # 4. Firmware
        if fw:
            resultado["firmware"] = str(fw).strip()

        # 5. Contadores (Geral e Detalhados)
        if cont_principal is not None:
            try:
                resultado["contador"] = int(str(cont_principal).strip())
            except (ValueError, TypeError):
                pass

        detalhados = {}
        if total1 is not None:
            try:
                t1_val = int(str(total1).strip())
                detalhados["Total"] = t1_val
                if resultado["contador"] is None:
                    resultado["contador"] = t1_val
            except (ValueError, TypeError):
                pass

        if print_val is not None:
            try:
                detalhados["Impressão"] = int(str(print_val).strip())
            except (ValueError, TypeError):
                pass

        if copia_val is not None:
            try:
                detalhados["Cópia"] = int(str(copia_val).strip())
            except (ValueError, TypeError):
                pass

        if scan_val is not None:
            try:
                detalhados["Scanner"] = int(str(scan_val).strip())
            except (ValueError, TypeError):
                pass

        if duplex_val is not None:
            try:
                detalhados["Duplex"] = int(str(duplex_val).strip())
            except (ValueError, TypeError):
                pass

        if fax_val is not None:
            try:
                detalhados["Fax/Recebimento"] = int(str(fax_val).strip())
            except (ValueError, TypeError):
                pass

        resultado["contadores_detalhados"] = detalhados

        # 6. Suprimentos (Toner e Tambor)
        supplies_lista = self._processar_suprimentos_direto(
            desc_toner, max_toner, lvl_toner, resultado["contador"]
        )
        resultado["supplies"] = supplies_lista
        resultado["suprimentos"] = supplies_lista

        return resultado

    # --------------------------------------------------------
    # SUPRIMENTOS CANON
    # --------------------------------------------------------
    def _processar_suprimentos_direto(
        self, desc_toner: Any, max_toner: Any, lvl_toner: Any, contador_total: Optional[int]
    ) -> list:
        supplies = []

        if desc_toner:
            desc_str = str(desc_toner).strip()
            pct = None
            max_val = 100
            lvl_val = 0
            try:
                if max_toner is not None and int(max_toner) > 0 and lvl_toner is not None:
                    max_val = int(max_toner)
                    lvl_val = int(lvl_toner)
                    if max_val == 100:
                        pct = max(0, min(100, lvl_val))
                    else:
                        pct = max(0, min(100, int((lvl_val / max_val) * 100)))
            except (ValueError, TypeError):
                pct = 0

            restante = lvl_val if pct is not None else 0
            consumido = max(0, max_val - restante)

            part_num = "T06" if "T06" in desc_str.upper() else "Toner Canon"

            supplies.append({
                "tipo": "toner",
                "nome": "Toner",
                "descricao": desc_str,
                "percentual": pct if pct is not None else 0,
                "capacidade": max_val,
                "restante": restante,
                "consumido": consumido,
                "condicao": "OK" if (pct is not None and pct > 10) else "BAIXO",
                "numero_serie": None,
                "part_number": part_num,
            })

        # 2. Unidade de Imagem / Tambor (Drum Unit)
        # Canon iR1643 utiliza Drum Unit T06 (0388C001BA / nominal 40.000 páginas)
        if contador_total is not None and contador_total >= 0:
            VIDA_UTIL_TAMBOR_T06 = 40000
            consumido_paginas = contador_total
            restante_paginas = max(0, VIDA_UTIL_TAMBOR_T06 - consumido_paginas)
            pct_tambor = max(0, min(100, int((restante_paginas / VIDA_UTIL_TAMBOR_T06) * 100)))

            supplies.append({
                "tipo": "unidade_imagem",
                "nome": "Unidade de imagem",
                "descricao": "Canon Drum Unit T06",
                "percentual": pct_tambor,
                "capacidade": VIDA_UTIL_TAMBOR_T06,
                "restante": restante_paginas,
                "consumido": consumido_paginas,
                "condicao": "OK" if pct_tambor > 15 else "SUBSTITUIR EM BREVE",
                "numero_serie": None,
                "part_number": "Drum T06",
                "garantia": True if pct_tambor >= 50 else False,
            })

        return supplies


# ============================================================
# FUNÇÃO DE CONVENIÊNCIA PÚBLICA
# ============================================================

async def coletar_canon(ip: str, community: str = "public") -> Dict[str, Any]:
    """Coleta e normaliza dados de equipamentos Canon."""
    coletor = CanonCollector(ip, community)
    return await coletor.coletar()
