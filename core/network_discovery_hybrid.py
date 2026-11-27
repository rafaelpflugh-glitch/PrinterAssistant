"""
============================================================
PRINTER ASSISTANT — MOTOR DE DESCOBERTA HÍBRIDA DE REDE
(core/network_discovery_hybrid.py)
============================================================

100% Python padrão (zero dependências externas):
  1. Auto-detecção de TODAS as placas de rede IPv4 ativas do PC (Wi-Fi + Ethernet)
  2. WS-Discovery Multicast (UDP 3702 — 239.255.255.250)
  3. mDNS / Bonjour Multicast (UDP 5353 — 224.0.0.251)
  4. SNMPv2c Broadcast (UDP 161 -> x.x.x.255) com verificação rápida Printer MIB
  5. Varredura paralela TCP 9100 (sem disparar 254 subprocessos ping.exe!)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ipaddress
import re
import socket
import struct
import subprocess
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

_INTERFACES_IGNORAR = ("loopback", "vethernet", "wsl", "vmware", "virtualbox", "teredo", "isatap")


def _ber_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    enc = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(enc)]) + enc


def _ber_tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _ber_len(len(value)) + value


def _ber_int(val: int) -> bytes:
    if val == 0:
        return _ber_tlv(0x02, b"\x00")
    enc = val.to_bytes((val.bit_length() + 7) // 8, "big")
    if enc[0] & 0x80:
        enc = b"\x00" + enc
    return _ber_tlv(0x02, enc)


def _ber_oid(oid_str: str) -> bytes:
    partes = [int(x) for x in oid_str.strip(".").split(".") if x.strip()]
    body = bytearray([partes[0] * 40 + partes[1]])
    for sub in partes[2:]:
        if sub == 0:
            body.append(0)
        else:
            pilha = []
            t = sub
            while t > 0:
                pilha.insert(0, t & 0x7F)
                t >>= 7
            for i in range(len(pilha) - 1):
                body.append(pilha[i] | 0x80)
            body.append(pilha[-1])
    return _ber_tlv(0x06, bytes(body))


def _montar_snmp_get(oid: str, community: str = "public", req_id: int = 7741, version: int = 1) -> bytes:
    """version=1 -> SNMPv2c; version=0 -> SNMPv1."""
    vb = _ber_tlv(0x30, _ber_oid(oid) + b"\x05\x00")
    pdu = _ber_tlv(0xA0, _ber_int(req_id) + _ber_int(0) + _ber_int(0) + _ber_tlv(0x30, vb))
    return _ber_tlv(0x30, _ber_int(version) + _ber_tlv(0x04, community.encode("utf-8")) + pdu)


def _ber_read_tlv(data: bytes, pos: int) -> Tuple[int, bytes, int]:
    if pos >= len(data):
        raise ValueError("BER EOF")
    tag = data[pos]
    pos += 1
    if pos >= len(data):
        raise ValueError("BER length EOF")
    b0 = data[pos]
    pos += 1
    if b0 < 0x80:
        length = b0
    else:
        nbytes = b0 & 0x7F
        if nbytes == 0 or pos + nbytes > len(data):
            raise ValueError("BER invalid length")
        length = int.from_bytes(data[pos : pos + nbytes], "big")
        pos += nbytes
    end = pos + length
    if end > len(data):
        raise ValueError("BER truncated value")
    return tag, data[pos:end], end


def _extrair_valor_snmp_response(data: bytes) -> Optional[Any]:
    """Decodifica o primeiro VarBind de um SNMP GetResponse (v1/v2c)."""
    try:
        tag, msg, _ = _ber_read_tlv(data, 0)
        if tag != 0x30:
            return None
        p = 0
        _, _, p = _ber_read_tlv(msg, p)       # version
        _, _, p = _ber_read_tlv(msg, p)       # community
        pdu_tag, pdu, _ = _ber_read_tlv(msg, p)
        if pdu_tag != 0xA2:                   # GetResponse-PDU
            return None
        pp = 0
        _, _, pp = _ber_read_tlv(pdu, pp)     # request-id
        _, err_b, pp = _ber_read_tlv(pdu, pp) # error-status
        if int.from_bytes(err_b, "big", signed=True) != 0:
            return None
        _, _, pp = _ber_read_tlv(pdu, pp)     # error-index
        vb_list_tag, vb_list, _ = _ber_read_tlv(pdu, pp)
        if vb_list_tag != 0x30:
            return None
        vb_tag, vb, _ = _ber_read_tlv(vb_list, 0)
        if vb_tag != 0x30:
            return None
        vp = 0
        _, _, vp = _ber_read_tlv(vb, vp)      # OID
        val_tag, val_bytes, _ = _ber_read_tlv(vb, vp)

        if val_tag in (0x05, 0x80, 0x81, 0x82):  # NULL / NoSuchObject / NoSuchInstance / EndOfMib
            return None
        if val_tag == 0x02:  # INTEGER (signed)
            return int.from_bytes(val_bytes, "big", signed=True)
        if val_tag in (0x41, 0x42, 0x43, 0x46):  # Counter32 / Gauge32 / TimeTicks / Counter64
            return int.from_bytes(val_bytes, "big", signed=False)
        if val_tag == 0x04:  # OCTET STRING
            texto = val_bytes.decode("utf-8", errors="ignore").replace("\x00", "").strip()
            if not texto:
                texto = val_bytes.decode("latin-1", errors="ignore").replace("\x00", "").strip()
            return texto or None
        return None
    except Exception:
        return None


def _snmp_get_sock(
    sock: socket.socket,
    ip: str,
    oid: str,
    community: str = "public",
    version: int = 1,
    req_id: int = 7750,
) -> Optional[Any]:
    pkt = _montar_snmp_get(oid, community=community, req_id=req_id, version=version)
    try:
        sock.sendto(pkt, (ip, 161))
        data, _ = sock.recvfrom(4096)
        return _extrair_valor_snmp_response(data)
    except Exception:
        return None


def coletar_identificacao_snmp_rapida(
    ip: str,
    community: str = "public",
    timeout: float = 0.6,
) -> Dict[str, Any]:
    """
    Coleta modelo, serial, firmware, sysDescr e contador via socket UDP SNMP puro
    (~30-80 ms por impressora, zero bloqueio do event loop, zero pysnmp/SnmpEngine).
    Suporta Lexmark, Canon, TSC, HP, Brother, Ricoh, etc. com fallback SNMPv2c -> SNMPv1.
    """
    resultado: Dict[str, Any] = {
        "ativo": False,
        "descricao": None,
        "modelo": None,
        "serial": None,
        "firmware": None,
        "contador": None,
        "fabricante_dica": None,
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)

            versao = 1  # SNMPv2c
            descricao = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.1.1.0", community, version=1, req_id=7801)
            if descricao is None:
                # Fallback para SNMPv1 (impressoras mais antigas ou térmicas)
                descricao = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.1.1.0", community, version=0, req_id=7802)
                if descricao is not None:
                    versao = 0

            # Se nem sysDescr respondeu, tenta prtMarkerLifeCount antes de desistir
            contador = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.43.10.2.1.4.1.1", community, version=versao, req_id=7803)
            if descricao is None and contador is None:
                return resultado

            resultado["ativo"] = True
            d_str = str(descricao).strip() if descricao is not None else ""
            resultado["descricao"] = d_str or None
            d_low = d_str.lower()

            modelo = None
            serial = None
            firmware = None

            if "canon" in d_low:
                resultado["fabricante_dica"] = "Canon"
                modelo_c = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.25.3.2.1.3.1", community, version=versao, req_id=7804)
                if not modelo_c:
                    modelo_c = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.1602.1.1.1.1.0", community, version=versao, req_id=7805)
                modelo = str(modelo_c).strip() if modelo_c else None
                serial = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.1602.1.2.1.4.0", community, version=versao, req_id=7806)
                if not serial:
                    serial = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.43.5.1.1.17.1", community, version=versao, req_id=7807)
                firmware = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.1602.1.1.1.4.0", community, version=versao, req_id=7808)
                cont_c = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.1602.1.11.1.4.1.4.101", community, version=versao, req_id=7809)
                if isinstance(cont_c, int):
                    contador = cont_c
            else:
                # Tenta Enterprise MIB Lexmark se parecer Lexmark ou genérico
                if "lexmark" in d_low or not any(m in d_low for m in ("ttp", "tsc", "zebra", "hp ", "brother", "ricoh", "epson")):
                    modelo = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.641.2.1.2.1.2.1", community, version=versao, req_id=7810)
                    serial = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.641.2.1.2.1.6.1", community, version=versao, req_id=7811)
                    firmware = _snmp_get_sock(sock, ip, "1.3.6.1.4.1.641.2.1.2.1.4.1", community, version=versao, req_id=7812)

                if not serial:
                    serial = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.43.5.1.1.17.1", community, version=versao, req_id=7813)

                if not modelo:
                    hr_mod = _snmp_get_sock(sock, ip, "1.3.6.1.2.1.25.3.2.1.3.1", community, version=versao, req_id=7814)
                    if hr_mod:
                        modelo = str(hr_mod).strip()

            # Fallbacks de modelo via sysDescr (espelhando core/snmp.py)
            if not modelo and d_str:
                m_tsc = re.search(r"\b(TTP\s*[-_]?\s*\d{3}[A-Za-z0-9]*)\b", d_str, re.IGNORECASE)
                if m_tsc:
                    modelo = f"TSC {m_tsc.group(1).upper()}"
                else:
                    m_lex = re.search(r"(?:Lexmark\s+)?([A-Z]{2}\s*\d{3}[A-Za-z0-9]*)", d_str, re.IGNORECASE)
                    if m_lex and "lexmark" in d_low:
                        modelo = m_lex.group(0).strip()
                    elif "canon" in d_low:
                        m_can = re.search(r"Canon\s+([^/,\r\n]+)", d_str, re.IGNORECASE)
                        modelo = f"Canon {m_can.group(1).strip()}" if m_can else d_str.split("/")[0].strip()
                    else:
                        parts = re.split(r"\bversion\b|\bv\.\b|\bver\b", d_str, flags=re.IGNORECASE)[0].strip(" :-")
                        if parts and not parts.lower().startswith("speed"):
                            modelo = parts

            if serial is not None:
                s_str = str(serial).strip()
                s_str = re.sub(r"-\d+-\d+$", "", s_str)
                if not s_str or re.fullmatch(r"0+", s_str):
                    s_str = None
                serial = s_str

            if not firmware and d_str:
                m_fw = re.search(r"\bversion\s+([A-Za-z0-9._-]+)", d_str, re.IGNORECASE)
                if m_fw:
                    firmware = m_fw.group(1).strip()

            if contador is not None:
                try:
                    contador = int(str(contador).strip())
                except (ValueError, TypeError):
                    contador = None

            resultado["modelo"] = str(modelo).strip() if modelo else None
            resultado["serial"] = serial
            resultado["firmware"] = str(firmware).strip() if firmware else None
            resultado["contador"] = contador
    except Exception:
        pass

    return resultado


def eh_impressora_snmp_rapido(ip: str, community: str = "public", timeout: float = 0.7) -> bool:
    """
    Verifica em milissegundos se um host responde à Printer MIB (prtMarkerLifeCount)
    ou possui marca conhecida de impressora no sysDescr. Evita confundir PCs/roteadores.
    """
    pkt_desc = _montar_snmp_get("1.3.6.1.2.1.1.1.0", community=community, req_id=7742)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            s.sendto(pkt_desc, (ip, 161))
            data, _ = s.recvfrom(4096)
        txt = data.decode("latin-1", errors="ignore").lower()
        marcas = (
            "lexmark", "canon", "hp ", "hewlett", "brother", "ricoh", "kyocera",
            "xerox", "epson", "konica", "samsung", "sharp", "oki", "ttp", "tsc",
            "zebra", "elgin", "argox", "datamax", "pantum", "toshiba", "print", "mfp",
        )
        if any(m in txt for m in marcas):
            return True
    except Exception:
        return False

    # Confirmação extra: consulta prtMarkerLifeCount (RFC-3805)
    pkt_mib = _montar_snmp_get("1.3.6.1.2.1.43.10.2.1.4.1.1", community=community, req_id=7743)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            s.sendto(pkt_mib, (ip, 161))
            data, _ = s.recvfrom(4096)
        # Se não retornou NoSuchObject (0x80) nem NoSuchInstance (0x81)
        return len(data) > 15 and (b"\x80\x00" not in data and b"\x81\x00" not in data)
    except Exception:
        return False


def detectar_subredes_ativas(ip_principal: str = "") -> List[Dict[str, str]]:
    """Detecta todas as sub-redes IPv4 reais ativas no Windows (Wi-Fi e Ethernet)."""
    subredes: List[Dict[str, str]] = []
    vistas: Set[str] = set()

    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-NetIPAddress -AddressFamily IPv4 | "
            "Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | "
            "ForEach-Object { \"$($_.IPAddress)|$($_.InterfaceAlias)\" }",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=4, creationflags=0x08000000)
        for linha in proc.stdout.splitlines():
            partes = linha.strip().split("|")
            if len(partes) < 2:
                continue
            ip_loc, alias = partes[0].strip(), partes[1].strip()
            if any(ig in alias.lower() for ig in _INTERFACES_IGNORAR) or ip_loc.startswith("192.168.56."):
                continue
            try:
                net = ipaddress.IPv4Network(f"{ip_loc}/24", strict=False)
                cidr = str(net)
                if cidr not in vistas:
                    vistas.add(cidr)
                    subredes.append({
                        "ip_local": ip_loc,
                        "prefixo": ".".join(ip_loc.split(".")[:3]),
                        "cidr": cidr,
                        "broadcast": str(net.broadcast_address),
                        "interface": alias,
                    })
            except ValueError:
                continue
    except Exception:
        pass

    if ip_principal:
        try:
            net = ipaddress.IPv4Network(f"{ip_principal}/24", strict=False)
            cidr = str(net)
            if cidr not in vistas:
                vistas.add(cidr)
                subredes.insert(0, {
                    "ip_local": ip_principal,
                    "prefixo": ".".join(ip_principal.split(".")[:3]),
                    "cidr": cidr,
                    "broadcast": str(net.broadcast_address),
                    "interface": "Interface Principal",
                })
            else:
                # Garante que a sub-rede principal apareça primeiro
                subredes.sort(key=lambda s: 0 if s["cidr"] == cidr else 1)
        except ValueError:
            pass

    return subredes


def descobrir_ws_discovery(subredes: Optional[List[Dict[str, str]]] = None, timeout: float = 1.2) -> Set[str]:
    """Probe SOAP WS-Discovery (UDP 3702 multicast 239.255.255.250) em todas as interfaces ativas."""
    ips: Set[str] = set()
    probe = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" '
        'xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery" '
        'xmlns:wsdp="http://schemas.xmlsoap.org/ws/2006/02/devprof">'
        "<soap:Header>"
        "<wsa:To>urn:schemas-xmlsoap-org:ws:2005:04/discovery</wsa:To>"
        "<wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>"
        f"<wsa:MessageID>urn:uuid:{uuid.uuid4()}</wsa:MessageID>"
        "</soap:Header>"
        "<soap:Body><wsd:Probe><wsd:Types>wsdp:Device</wsd:Types></wsd:Probe></soap:Body>"
        "</soap:Envelope>"
    ).encode("utf-8")

    interfaces_locais = [sr["ip_local"] for sr in (subredes or []) if sr.get("ip_local")] or [None]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(0.3)
            for ip_if in interfaces_locais:
                try:
                    if ip_if:
                        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip_if))
                    sock.sendto(probe, ("239.255.255.250", 3702))
                except OSError:
                    continue
            fim = time.time() + timeout
            while time.time() < fim:
                try:
                    data, addr = sock.recvfrom(8192)
                    txt = data.decode("utf-8", errors="ignore").lower()
                    if any(k in txt for k in ("print", "lexmark", "canon", "mfp", "scan", "wsdp:device")):
                        ips.add(addr[0])
                except socket.timeout:
                    continue
                except OSError:
                    break
    except Exception:
        pass
    return ips


def descobrir_mdns(subredes: Optional[List[Dict[str, str]]] = None, timeout: float = 1.2) -> Set[str]:
    """Consulta serviços de impressão via mDNS/Bonjour (UDP 5353) em todas as interfaces ativas."""
    ips: Set[str] = set()
    servicos = ("_pdl-datastream._tcp.local", "_ipp._tcp.local", "_printer._tcp.local")
    interfaces_locais = [sr["ip_local"] for sr in (subredes or []) if sr.get("ip_local")] or [None]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(0.3)
            for ip_if in interfaces_locais:
                try:
                    if ip_if:
                        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip_if))
                    for srv in servicos:
                        qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in srv.split(".")) + b"\x00"
                        pkt = struct.pack("!HHHHHH", 0, 0, 1, 0, 0, 0) + qname + struct.pack("!HH", 12, 1)
                        sock.sendto(pkt, ("224.0.0.251", 5353))
                except OSError:
                    continue
            fim = time.time() + timeout
            while time.time() < fim:
                try:
                    _data, addr = sock.recvfrom(4096)
                    if not addr[0].startswith(("127.", "169.254.")):
                        ips.add(addr[0])
                except socket.timeout:
                    continue
                except OSError:
                    break
    except Exception:
        pass
    return ips


def descobrir_snmp_broadcast(subredes: List[Dict[str, str]], community: str = "public", timeout: float = 1.2) -> Set[str]:
    """Envia SNMPv2c GET sysDescr em broadcast nas sub-redes ativas."""
    ips: Set[str] = set()
    pkt = _montar_snmp_get("1.3.6.1.2.1.1.1.0", community=community, req_id=7741)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.3)
            for sr in subredes:
                try:
                    sock.sendto(pkt, (sr["broadcast"], 161))
                except OSError:
                    pass
            fim = time.time() + timeout
            while time.time() < fim:
                try:
                    data, addr = sock.recvfrom(4096)
                    if len(data) > 12:
                        ips.add(addr[0])
                except socket.timeout:
                    continue
                except OSError:
                    break
    except Exception:
        pass
    return ips


def varrer_tcp_9100_subredes(subredes: List[Dict[str, str]], timeout: float = 0.30) -> Set[str]:
    """Varredura paralela leve na porta RAW 9100 em todas as sub-redes ativas (sem ping.exe!)."""
    alvos: List[str] = []
    ips_locais = {sr["ip_local"] for sr in subredes if sr.get("ip_local")}
    for sr in subredes:
        pref = sr["prefixo"]
        for i in range(1, 255):
            h = f"{pref}.{i}"
            if h not in ips_locais:
                alvos.append(h)

    def _check(host: str) -> Optional[str]:
        try:
            with socket.create_connection((host, 9100), timeout=timeout):
                return host
        except OSError:
            return None

    encontrados: Set[str] = set()
    if not alvos:
        return encontrados
    with ThreadPoolExecutor(max_workers=96) as pool:
        for res in pool.map(_check, alvos):
            if res:
                encontrados.add(res)
    return encontrados


def executar_descoberta_hibrida(
    ip_principal: str = "",
    forcar_varredura_tcp: bool = False,
) -> Dict[str, object]:
    """
    Executa a descoberta híbrida completa em paralelo:
    - Fase rápida (~1.3s): Interfaces PC + WS-Discovery + mDNS + SNMP Broadcast
    - Fase TCP 9100 (sempre executada em paralelo leve sem ping.exe para garantir
      equipamentos que ignoram broadcast)
    """
    subredes = detectar_subredes_ativas(ip_principal=ip_principal)
    ips_locais = {sr["ip_local"] for sr in subredes if sr.get("ip_local")}
    if ip_principal:
        ips_locais.add(ip_principal)

    origens: Dict[str, Set[str]] = {}

    def _add(conjunto: Set[str], tag: str):
        for h in conjunto:
            if h not in ips_locais and not h.startswith(("127.", "169.254.")):
                origens.setdefault(h, set()).add(tag)

    # 1. Multicast/Broadcast + varredura TCP 9100 TUDO EM PARALELO (~1.8-2.4s total!)
    timeout_tcp = 0.45 if forcar_varredura_tcp else 0.28
    with ThreadPoolExecutor(max_workers=4) as pool:
        f_wsd = pool.submit(descobrir_ws_discovery, subredes, 1.0)
        f_mdns = pool.submit(descobrir_mdns, subredes, 1.0)
        f_snmp = pool.submit(descobrir_snmp_broadcast, subredes, "public", 1.0)
        f_tcp = pool.submit(varrer_tcp_9100_subredes, subredes, timeout_tcp)
        _add(f_wsd.result(), "WSD")
        _add(f_mdns.result(), "mDNS")
        _add(f_snmp.result(), "SNMP-Bcast")
        achados_tcp = f_tcp.result()
        _add(achados_tcp, "TCP-9100")

    return {
        "subredes": subredes,
        "origens": origens,
        "ips_tcp_9100": achados_tcp,
    }
