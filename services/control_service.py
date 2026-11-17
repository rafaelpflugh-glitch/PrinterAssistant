import os
import socket
import time
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

try:
    from pysnmp.hlapi import (
        SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
        ObjectType, ObjectIdentity, setCmd, Integer32, OctetString
    )
    SNMP_DISPONIVEL = True
except ImportError:
    SNMP_DISPONIVEL = False

class ControlError(Exception):
    pass

class PJLService:
    PORTA_PADRAO = 9100
    TIMEOUT = 5.0

    def __init__(self, ip):
        if not ip:
            raise ControlError("IP não fornecido.")
        self.ip = ip

    def _enviar(self, comando_pjl, aguardar_resposta=False):
        comando_bytes = comando_pjl.encode('utf-8')
        
        if aguardar_resposta:
            pacote = b"\x1B%-12345X@PJL\r\n" + comando_bytes + b"\r\n"
        else:
            pacote = b"\x1B%-12345X@PJL\r\n" + comando_bytes + b"\r\n\x1B%-12345X\r\n"

        resposta = ""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.TIMEOUT)
                s.connect((self.ip, self.PORTA_PADRAO))
                s.sendall(pacote)

                if aguardar_resposta:
                    time.sleep(1.0)
                    while True:
                        try:
                            dados = s.recv(4096)
                            if not dados:
                                break
                            resposta += dados.decode('utf-8', errors='ignore')
                        except socket.timeout:
                            break
        except Exception as erro:
            raise ControlError(f"Falha de injeção na porta 9100: {erro}")

        return resposta.strip()

    def enviar_firmware(self, caminho_arquivo_fls):
        if not os.path.exists(caminho_arquivo_fls):
            raise ControlError(f"Arquivo não encontrado: {caminho_arquivo_fls}")
        CHUNK_SIZE = 65536 
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15.0)
                s.connect((self.ip, self.PORTA_PADRAO))
                with open(caminho_arquivo_fls, 'rb') as f:
                    while True:
                        bloco = f.read(CHUNK_SIZE)
                        if not bloco: break
                        s.sendall(bloco)
        except Exception as erro:
            raise ControlError(f"Falha na transferência do firmware: {erro}")
        return "Transferência do firmware concluída. A máquina irá reiniciar."

    def alterar_mensagem_painel(self, mensagem="MANUTENCAO TI"):
        msg_limpa = str(mensagem)[:16].upper()
        self._enviar(f'@PJL RDYMSG DISPLAY="{msg_limpa}"')

    def resetar_ambiente_nvram(self):
        self._enviar("@PJL RESET")

    def inicializar_spooler(self):
        self._enviar("@PJL INITIALIZE")

    def finalizar_trabalho_preso(self):
        self._enviar("@PJL EOJ")

    def formatar_memoria_flash(self):
        self._enviar('@PJL FSINIT VOLUME="0:"')

    def definir_tamanho_papel(self, tamanho="A4"):
        self._enviar(f"@PJL DEFAULT PAPER={tamanho.upper()}")

    def definir_tipo_midia(self, tipo="REGULAR"):
        self._enviar(f"@PJL DEFAULT MEDIATYPE={tipo.upper()}")

    def configurar_duplex(self, ativar=True):
        estado = "ON" if ativar else "OFF"
        self._enviar(f"@PJL DEFAULT DUPLEX={estado}")

    def definir_economia_toner(self, ativar=False):
        estado = "ON" if ativar else "OFF"
        self._enviar(f"@PJL DEFAULT ECONOMODE={estado}")

    def definir_densidade(self, nivel=3):
        nivel = max(1, min(5, int(nivel)))
        self._enviar(f"@PJL DEFAULT DENSITY={nivel}")
        
    def bloquear_painel_fisico(self, bloquear=True):
        estado = "LOCK" if bloquear else "UNLOCK"
        self._enviar(f"@PJL DEFAULT LOPANEL={estado}")

    def obter_status(self):
        return self._enviar("@PJL INFO STATUS", aguardar_resposta=True)

    def obter_todas_variaveis(self):
        return self._enviar("@PJL INFO VARIABLES", aguardar_resposta=True)

    def obter_crash_logs(self):
        return self._enviar("@PJL INFO FAULT", aguardar_resposta=True)

    def injetar_raw(self, comando):
        comando_limpo = comando.strip()
        if not comando_limpo.startswith("@PJL"):
            comando_limpo = f"@PJL {comando_limpo}"
        
        if "INFO " in comando_limpo.upper():
            return self._enviar(comando_limpo, aguardar_resposta=True)
        else:
            self._enviar(comando_limpo)
            return f"Comando enviado com sucesso."

class SNMPService:
    PORTA = 161
    def __init__(self, ip, comunidade_escrita="private"):
        if not SNMP_DISPONIVEL:
            raise ControlError("pysnmp não instalado.")
        self.ip = ip
        self.comunidade = comunidade_escrita

    def _set_oid(self, oid_string, valor, tipo_valor):
        errorIndication, errorStatus, errorIndex, varBinds = next(
            setCmd(
                SnmpEngine(),
                CommunityData(self.comunidade, mpModel=1),
                UdpTransportTarget((self.ip, self.PORTA), timeout=3.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oid_string), tipo_valor(valor))
            )
        )
        if errorIndication or errorStatus:
            raise ControlError(f"Erro SNMP. A comunidade '{self.comunidade}' tem permissão de escrita habilitada?")
        return True

    def reboot_frio(self):
        return self._set_oid('1.3.6.1.2.1.43.5.1.1.3.1', 2, Integer32)

    def alterar_hostname(self, novo_nome):
        return self._set_oid('1.3.6.1.2.1.1.5.0', str(novo_nome), OctetString)

class WebService:
    def __init__(self, ip, protocolo="https"):
        self.ip = ip
        self.base_url = f"{protocolo}://{self.ip}"
        self.session = requests.Session()

    def resetar_fusor_lexmark(self):
        endpoint = f"{self.base_url}/cgi-bin/dynamic/config/maintenance_reset.html"
        payload = {"ResetMaintenance": "1", "Submit": "Submit"}
        try:
            resp = self.session.post(endpoint, data=payload, timeout=5.0, verify=False)
            return resp.status_code == 200
        except:
            raise ControlError("Falha ao enviar POST para reset.")

    def restaurar_padroes_fabrica(self):
        endpoint = f"{self.base_url}/cgi-bin/dynamic/config/factory_defaults.html"
        payload = {"RestoreDefaults": "All", "Submit": "Restore"}
        try:
            resp = self.session.post(endpoint, data=payload, timeout=5.0, verify=False)
            return resp.status_code == 200
        except:
            raise ControlError("Falha ao enviar POST.")

    def alternar_scanner_adf(self, habilitar=True):
        endpoint = f"{self.base_url}/cgi-bin/dynamic/config/diagnostic_setup.html"
        estado = "Enable" if habilitar else "Disable"
        payload = {"ScannerDisable": estado, "Submit": "Submit"}
        try:
            resp = self.session.post(endpoint, data=payload, timeout=5.0, verify=False)
            if resp.status_code == 200:
                return f"Scanner/ADF alterado para: {estado}"
            raise ControlError("Acesso negado ou rota inválida.")
        except requests.exceptions.RequestException as e:
            raise ControlError(f"Falha ao enviar comando para o Scanner: {e}")
