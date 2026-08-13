"""
Printer Assistant - Printer Commands

Camada de ações executáveis sobre a impressora.

Não contém:
- descoberta de dispositivos;
- identificação principal;
- SNMP;
- SYSDEBUG.

Responsável por:
- conexão RAW/PJL;
- consultas PJL;
- interpretação de INFO CONFIG;
- abertura de relatórios web;
- preparação para ações reais.
"""

from __future__ import annotations

import re
import socket
import webbrowser
from dataclasses import dataclass
from typing import Optional


# =========================================================
# CONFIGURAÇÃO
# =========================================================

PORTA_RAW = 9100
TIMEOUT = 5

UNIVERSAL_RESET = b"\x1b%-12345X"


# =========================================================
# RESULTADO
# =========================================================

@dataclass
class CommandResult:

    sucesso: bool
    comando: str
    mensagem: str
    resposta: str = ""

    def to_dict(self):

        return {
            "sucesso": self.sucesso,
            "comando": self.comando,
            "mensagem": self.mensagem,
            "resposta": self.resposta,
        }


# =========================================================
# COMMANDS
# =========================================================

class PrinterCommands:

    def __init__(
        self,
        ip: str,
        porta: int = PORTA_RAW,
        timeout: int = TIMEOUT,
    ):

        self.ip = str(ip).strip()
        self.porta = porta
        self.timeout = timeout

    # =====================================================
    # CONEXÃO
    # =====================================================

    def testar_conexao(self) -> CommandResult:

        comando = "testar_conexao"

        try:

            with socket.create_connection(
                (
                    self.ip,
                    self.porta,
                ),
                timeout=self.timeout,
            ):

                return CommandResult(
                    sucesso=True,
                    comando=comando,
                    mensagem=(
                        f"RAW/PJL ativo em "
                        f"{self.ip}:{self.porta}"
                    ),
                )

        except Exception as erro:

            return CommandResult(
                sucesso=False,
                comando=comando,
                mensagem=(
                    f"Não foi possível conectar "
                    f"em {self.ip}:{self.porta}: "
                    f"{erro}"
                ),
            )

    # =====================================================
    # ENVIO PJL
    # =====================================================

    def enviar_pjl(
        self,
        comando: str,
        aguardar_resposta: bool = True,
    ) -> CommandResult:

        if not comando:

            return CommandResult(
                sucesso=False,
                comando="pjl",
                mensagem="Comando PJL vazio.",
            )

        payload = (
            UNIVERSAL_RESET
            + comando.encode(
                "ascii",
                errors="ignore",
            )
            + b"\r\n"
            + UNIVERSAL_RESET
        )

        resposta = b""
        sock: Optional[socket.socket] = None

        try:

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )

            sock.settimeout(
                self.timeout
            )

            sock.connect(
                (
                    self.ip,
                    self.porta,
                )
            )

            sock.sendall(
                payload
            )

            if aguardar_resposta:

                while True:

                    try:

                        parte = sock.recv(
                            4096
                        )

                    except socket.timeout:

                        break

                    if not parte:

                        break

                    resposta += parte

                    if len(parte) < 4096:

                        break

            texto = resposta.decode(
                "latin1",
                errors="ignore",
            )

            return CommandResult(
                sucesso=True,
                comando=comando,
                mensagem="Comando enviado.",
                resposta=texto,
            )

        except Exception as erro:

            return CommandResult(
                sucesso=False,
                comando=comando,
                mensagem=(
                    f"Erro enviando PJL: "
                    f"{erro}"
                ),
            )

        finally:

            if sock is not None:

                try:
                    sock.close()
                except Exception:
                    pass

    # =====================================================
    # CONSULTAS PJL
    # =====================================================

    def info_id(self) -> CommandResult:

        return self.enviar_pjl(
            "@PJL INFO ID"
        )

    def pagecount(self) -> CommandResult:

        return self.enviar_pjl(
            "@PJL INFO PAGECOUNT"
        )

    def info_config(self) -> CommandResult:

        return self.enviar_pjl(
            "@PJL INFO CONFIG"
        )

    def info_status(self) -> CommandResult:

        return self.enviar_pjl(
            "@PJL INFO STATUS"
        )

    # =====================================================
    # PARSER INFO CONFIG
    # =====================================================

    @staticmethod
    def _extrair_lista_enum(
        texto: str,
        nome: str,
    ) -> list[str]:

        padrao = re.compile(
            rf"{re.escape(nome)}\s+\[(\d+)\s+ENUMERATED\]"
            rf"(.*?)(?=\n[A-Z][A-Z0-9 _-]*"
            rf"(?:\s+\[\d+\s+ENUMERATED\])?|"
            rf"\n[A-Z][A-Z0-9 _-]*=|\Z)",
            re.IGNORECASE | re.DOTALL,
        )

        encontrado = padrao.search(
            texto
        )

        if not encontrado:

            return []

        quantidade = int(
            encontrado.group(1)
        )

        bloco = encontrado.group(2)

        itens = []

        for linha in bloco.splitlines():

            linha = linha.strip()

            if not linha:
                continue

            itens.append(
                linha
            )

        return itens[:quantidade]

    @staticmethod
    def _extrair_valor(
        texto: str,
        chave: str,
    ) -> Optional[str]:

        padrao = re.compile(
            rf"^{re.escape(chave)}=(.*)$",
            re.IGNORECASE | re.MULTILINE,
        )

        encontrado = padrao.search(
            texto
        )

        if not encontrado:

            return None

        return (
            encontrado.group(1)
            .strip()
        )

    @classmethod
    def parse_info_config(
        cls,
        texto: str,
    ) -> dict:

        if not texto:

            return {}

        texto = (
            str(texto)
            .replace(
                "\r\n",
                "\n",
            )
            .replace(
                "\r",
                "\n",
            )
        )

        dados = {}

        # -------------------------------------------------
        # BANDEJAS
        # -------------------------------------------------

        dados["bandejas"] = (
            cls._extrair_lista_enum(
                texto,
                "IN TRAYS",
            )
        )

        dados["saidas"] = (
            cls._extrair_lista_enum(
                texto,
                "OUTPUT BINS",
            )
        )

        dados["papeis"] = (
            cls._extrair_lista_enum(
                texto,
                "PAPERS",
            )
        )

        dados["linguagens"] = (
            cls._extrair_lista_enum(
                texto,
                "LANGUAGES",
            )
        )

        dados["ustatus"] = (
            cls._extrair_lista_enum(
                texto,
                "USTATUS",
            )
        )

        # -------------------------------------------------
        # HARDWARE
        # -------------------------------------------------

        disco = cls._extrair_valor(
            texto,
            "DISK",
        )

        memoria = cls._extrair_valor(
            texto,
            "MEMORY",
        )

        velocidade = cls._extrair_valor(
            texto,
            "ENGINE SPEED",
        )

        if disco is not None:

            try:
                dados["disco"] = int(
                    disco
                )
            except ValueError:
                dados["disco"] = disco

        if memoria is not None:

            try:
                dados["memoria"] = int(
                    memoria
                )
            except ValueError:
                dados["memoria"] = memoria

        if velocidade is not None:

            try:
                dados[
                    "velocidade_engine"
                ] = int(
                    velocidade
                )
            except ValueError:

                dados[
                    "velocidade_engine"
                ] = velocidade

        # -------------------------------------------------
        # FIRMWARES
        # -------------------------------------------------

        firmware = cls._extrair_valor(
            texto,
            "SYSTEM FIRMWARE VERSION",
        )

        scanner_firmware = (
            cls._extrair_valor(
                texto,
                "SCANNER FIRMWARE VERSION",
            )
        )

        scanner_boot = (
            cls._extrair_valor(
                texto,
                "SCANNER BOOT FIRMWARE VERSION",
            )
        )

        scanner_duplex = (
            cls._extrair_valor(
                texto,
                "SCANNER DUPLEX FIRMWARE VERSION",
            )
        )

        font_firmware = (
            cls._extrair_valor(
                texto,
                "FONT FIRMWARE VERSION",
            )
        )

        engine_firmware = (
            cls._extrair_valor(
                texto,
                "ENGINE FIRMWARE VERSION",
            )
        )

        if firmware:
            dados["firmware"] = firmware

        if scanner_firmware:
            dados[
                "scanner_firmware"
            ] = scanner_firmware

        if scanner_boot:
            dados[
                "scanner_boot_firmware"
            ] = scanner_boot

        if scanner_duplex:
            dados[
                "scanner_duplex_firmware"
            ] = scanner_duplex

        if font_firmware:
            dados[
                "font_firmware"
            ] = font_firmware

        if engine_firmware:
            dados[
                "engine_firmware"
            ] = engine_firmware

        # -------------------------------------------------
        # IDENTIFICAÇÃO
        # -------------------------------------------------

        serial = cls._extrair_valor(
            texto,
            "SERIAL NUMBER",
        )

        if serial:
            dados["serial"] = serial

        return dados

    # =====================================================
    # CONFIGURAÇÃO ESTRUTURADA
    # =====================================================

    def obter_configuracao(
        self,
    ) -> CommandResult:

        resultado = self.info_config()

        if not resultado.sucesso:

            return resultado

        configuracao = (
            self.parse_info_config(
                resultado.resposta
            )
        )

        import json

        resposta = json.dumps(
            configuracao,
            ensure_ascii=False,
            indent=2,
        )

        return CommandResult(
            sucesso=True,
            comando="obter_configuracao",
            mensagem=(
                "Configuração PJL interpretada."
            ),
            resposta=resposta,
        )

    # =====================================================
    # RELATÓRIOS WEB
    # =====================================================

    def abrir_relatorio(
        self,
        caminho: str,
        nome: str,
    ) -> CommandResult:

        url = (
            f"http://{self.ip}"
            f"{caminho}"
        )

        try:

            aberto = webbrowser.open(
                url
            )

            if not aberto:

                return CommandResult(
                    sucesso=False,
                    comando=nome,
                    mensagem=(
                        "O navegador não confirmou "
                        f"a abertura: {url}"
                    ),
                )

            return CommandResult(
                sucesso=True,
                comando=nome,
                mensagem=(
                    "Relatório aberto no navegador: "
                    f"{url}"
                ),
            )

        except Exception as erro:

            return CommandResult(
                sucesso=False,
                comando=nome,
                mensagem=(
                    f"Erro abrindo relatório: "
                    f"{erro}"
                ),
            )

    def abrir_pagina_configuracao(
        self,
    ) -> CommandResult:

        return self.abrir_relatorio(
            (
                "/cgi-bin/dynamic/printer/"
                "config/reports/deviceinfo.html"
            ),
            "pagina_configuracao",
        )

    def abrir_estatisticas(
        self,
    ) -> CommandResult:

        return self.abrir_relatorio(
            (
                "/cgi-bin/dynamic/printer/"
                "config/reports/"
                "devicestatistics.html"
            ),
            "estatisticas",
        )

    def abrir_status_web(
        self,
    ) -> CommandResult:

        return self.abrir_relatorio(
            (
                "/cgi-bin/dynamic/printer/"
                "PrinterStatus.html"
            ),
            "status_web",
        )

    # =====================================================
    # MENU
    # =====================================================

    def listar_comandos(self):

        return [
            {
                "id": "1",
                "nome": "Testar conexão",
            },
            {
                "id": "2",
                "nome": "Identificação PJL",
            },
            {
                "id": "3",
                "nome": "Contador PJL",
            },
            {
                "id": "4",
                "nome": "Status PJL",
            },
            {
                "id": "5",
                "nome": "Configuração PJL",
            },
            {
                "id": "6",
                "nome": "Configuração estruturada",
            },
            {
                "id": "7",
                "nome": "Página de configuração",
            },
            {
                "id": "8",
                "nome": "Estatísticas",
            },
            {
                "id": "9",
                "nome": "Status web",
            },
            {
                "id": "10",
                "nome": "Alterar papel",
            },
            {
                "id": "11",
                "nome": "Imprimir relatório de ativos",
            },
            {
                "id": "0",
                "nome": "Voltar",
            },
        ]

    # =====================================================
    # EXECUTAR
    # =====================================================

    def executar(
        self,
        opcao: str,
    ) -> CommandResult:

        opcao = str(
            opcao
        ).strip()

        if opcao == "1":
            return self.testar_conexao()

        if opcao == "2":
            return self.info_id()

        if opcao == "3":
            return self.pagecount()

        if opcao == "4":
            return self.info_status()

        if opcao == "5":
            return self.info_config()

        if opcao == "6":
            return self.obter_configuracao()

        if opcao == "7":
            return self.abrir_pagina_configuracao()

        if opcao == "8":
            return self.abrir_estatisticas()

        if opcao == "9":
            return self.abrir_status_web()

        if opcao == "10":

            return CommandResult(
                sucesso=False,
                comando="alterar_papel",
                mensagem=(
                    "Ainda não implementado. "
                    "Vamos primeiro identificar "
                    "a sintaxe PJL correta."
                ),
            )

        if opcao == "11":

            return CommandResult(
                sucesso=False,
                comando="imprimir_ativos",
                mensagem=(
                    "Ainda não implementado. "
                    "Vamos primeiro identificar "
                    "o mecanismo correto de impressão "
                    "dos relatórios."
                ),
            )

        if opcao == "0":

            return CommandResult(
                sucesso=True,
                comando="voltar",
                mensagem="Voltar.",
            )

        return CommandResult(
            sucesso=False,
            comando="desconhecido",
            mensagem="Opção inválida.",
        )


# =========================================================
# TESTE
# =========================================================

def teste():

    print()
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - COMANDOS"
    )
    print("=" * 72)
    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP não informado."
        )

        return

    comandos = PrinterCommands(
        ip
    )

    while True:

        print()
        print("=" * 72)
        print(
            f"IMPRESSORA: {comandos.ip}"
        )
        print("=" * 72)
        print()

        for item in comandos.listar_comandos():

            print(
                f"[{item['id']:>2}] "
                f"{item['nome']}"
            )

        print()

        opcao = input(
            "Escolha um comando: "
        ).strip()

        resultado = comandos.executar(
            opcao
        )

        print()
        print(
            resultado.mensagem
        )

        if resultado.resposta:

            print()
            print(
                "-" * 72
            )
            print(
                resultado.resposta
            )
            print(
                "-" * 72
            )

        if opcao == "0":

            break


if __name__ == "__main__":

    teste()