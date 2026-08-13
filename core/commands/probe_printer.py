"""
Printer Assistant - Printer Capability Probe

Ferramenta de diagnóstico NÃO DESTRUTIVA.

Objetivo:
    Descobrir tudo que a impressora declara através de:
        - PJL INFO
        - PJL CONFIG
        - PJL MEMORY
        - PJL PAGECOUNT
        - PJL STATUS
        - PJL VARIABLES
        - PJL USTATUS
        - HTTP/EWS
        - portas de rede conhecidas

IMPORTANTE:
    Este módulo NÃO altera configurações.
    Este módulo NÃO imprime.
    Este módulo NÃO grava na impressora.

Ele existe para descobrirmos primeiro
o que a impressora realmente suporta.
"""

from __future__ import annotations

import socket
import urllib.request
import urllib.error
from typing import Optional


PORTA_RAW = 9100
TIMEOUT_RAW = 5
TIMEOUT_WEB = 4


ESC = b"\x1b"

UNIVERSAL_RESET = b"\x1b%-12345X"


# =========================================================
# RESULTADO
# =========================================================

class ProbeResult:

    def __init__(
        self,
        nome: str,
        sucesso: bool,
        resposta: str = "",
        erro: str = "",
    ):

        self.nome = nome
        self.sucesso = sucesso
        self.resposta = resposta
        self.erro = erro

    def to_dict(self):

        return {
            "nome": self.nome,
            "sucesso": self.sucesso,
            "resposta": self.resposta,
            "erro": self.erro,
        }


# =========================================================
# PROBE
# =========================================================

class PrinterProbe:

    def __init__(
        self,
        ip: str,
        porta_raw: int = PORTA_RAW,
    ):

        self.ip = str(ip).strip()

        self.porta_raw = porta_raw

        self.resultados = []


    # =====================================================
    # PJL
    # =====================================================

    def enviar_pjl(
        self,
        comando: str,
        timeout: int = TIMEOUT_RAW,
    ) -> ProbeResult:

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
                timeout
            )

            sock.connect(
                (
                    self.ip,
                    self.porta_raw,
                )
            )

            sock.sendall(
                payload
            )

            while True:

                try:

                    parte = sock.recv(
                        8192
                    )

                except socket.timeout:

                    break

                if not parte:
                    break

                resposta += parte

                if len(parte) < 8192:
                    break

            texto = resposta.decode(
                "latin1",
                errors="ignore",
            )

            return ProbeResult(
                nome=comando,
                sucesso=True,
                resposta=texto,
            )

        except Exception as erro:

            return ProbeResult(
                nome=comando,
                sucesso=False,
                erro=str(erro),
            )

        finally:

            if sock is not None:

                try:
                    sock.close()

                except Exception:
                    pass


    # =====================================================
    # TESTAR RAW
    # =====================================================

    def testar_raw(self):

        try:

            with socket.create_connection(
                (
                    self.ip,
                    self.porta_raw,
                ),
                timeout=TIMEOUT_RAW,
            ):

                return True

        except Exception:

            return False


    # =====================================================
    # CATEGORIAS PJL
    # =====================================================

    def consultar_pjl(
        self,
        categoria: str,
    ):

        resultado = self.enviar_pjl(
            f"@PJL INFO {categoria}"
        )

        self.resultados.append(
            resultado
        )

        return resultado


    # =====================================================
    # HTTP
    # =====================================================

    def testar_http(
        self,
        esquema: str,
        porta: int,
    ) -> ProbeResult:

        url = (
            f"{esquema}://"
            f"{self.ip}:{porta}/"
        )

        try:

            requisicao = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent":
                        "PrinterAssistant-Probe/1.0"
                },
            )

            with urllib.request.urlopen(
                requisicao,
                timeout=TIMEOUT_WEB,
            ) as resposta:

                dados = resposta.read(
                    4096
                )

                texto = dados.decode(
                    "latin1",
                    errors="ignore",
                )

                return ProbeResult(
                    nome=url,
                    sucesso=True,
                    resposta=(
                        f"HTTP {resposta.status}\n"
                        f"Content-Type: "
                        f"{resposta.headers.get('Content-Type')}\n"
                        f"Server: "
                        f"{resposta.headers.get('Server')}\n\n"
                        f"{texto[:1000]}"
                    ),
                )

        except urllib.error.HTTPError as erro:

            return ProbeResult(
                nome=url,
                sucesso=False,
                erro=(
                    f"HTTP {erro.code}"
                ),
            )

        except Exception as erro:

            return ProbeResult(
                nome=url,
                sucesso=False,
                erro=str(erro),
            )


    # =====================================================
    # PORTA TCP
    # =====================================================

    def testar_porta(
        self,
        porta: int,
    ):

        try:

            with socket.create_connection(
                (
                    self.ip,
                    porta,
                ),
                timeout=2,
            ):

                return True

        except Exception:

            return False


    # =====================================================
    # PORTAS
    # =====================================================

    def descobrir_portas(self):

        portas = {

            80:
                "HTTP",

            443:
                "HTTPS",

            515:
                "LPR/LPD",

            631:
                "IPP",

            9100:
                "RAW",

            23:
                "TELNET",

            161:
                "SNMP",

            9400:
                "Lexmark Enhanced IP",

        }

        resultado = {}

        for porta, nome in portas.items():

            resultado[
                nome
            ] = {

                "porta":
                    porta,

                "aberta":
                    self.testar_porta(
                        porta
                    ),
            }

        return resultado


    # =====================================================
    # EXECUTAR DIAGNÓSTICO
    # =====================================================

    def executar(self):

        print()
        print("=" * 72)
        print(
            "PRINTER ASSISTANT - DIAGNÓSTICO DA IMPRESSORA"
        )
        print("=" * 72)

        print()

        print(
            f"IP: {self.ip}"
        )

        print(
            f"RAW: {self.ip}:{self.porta_raw}"
        )

        print()

        # -------------------------------------------------
        # RAW
        # -------------------------------------------------

        raw_ativo = self.testar_raw()

        print(
            "RAW/PJL:",
            "ATIVO"
            if raw_ativo
            else "INATIVO",
        )

        # -------------------------------------------------
        # PORTAS
        # -------------------------------------------------

        print()
        print("-" * 72)
        print(
            "PORTAS / PROTOCOLOS"
        )
        print("-" * 72)

        portas = (
            self.descobrir_portas()
        )

        for nome, dados in portas.items():

            print(
                f"{nome:<24}"
                f"porta {dados['porta']:<5}"
                f" "
                f"{'ABERTA' if dados['aberta'] else 'fechada'}"
            )

        # -------------------------------------------------
        # PJL
        # -------------------------------------------------

        categorias = (
            "ID",
            "CONFIG",
            "MEMORY",
            "PAGECOUNT",
            "STATUS",
            "VARIABLES",
            "USTATUS",
        )

        print()
        print("-" * 72)
        print(
            "PJL INFO"
        )
        print("-" * 72)

        for categoria in categorias:

            print()
            print(
                f"[PJL INFO {categoria}]"
            )

            resultado = (
                self.consultar_pjl(
                    categoria
                )
            )

            if resultado.sucesso:

                texto = (
                    resultado.resposta
                    .strip()
                )

                if texto:

                    print(
                        texto
                    )

                else:

                    print(
                        "(sem resposta)"
                    )

            else:

                print(
                    "ERRO:",
                    resultado.erro
                )

        # -------------------------------------------------
        # HTTP
        # -------------------------------------------------

        print()
        print("-" * 72)
        print(
            "WEB / EWS"
        )
        print("-" * 72)

        if portas.get(
            "HTTP",
            {}
        ).get(
            "aberta",
            False,
        ):

            resultado = (
                self.testar_http(
                    "http",
                    80,
                )
            )

            if resultado.sucesso:

                print(
                    "HTTP: acessível"
                )

                print(
                    resultado.resposta
                )

            else:

                print(
                    "HTTP:",
                    resultado.erro
                )

        if portas.get(
            "HTTPS",
            {}
        ).get(
            "aberta",
            False,
        ):

            resultado = (
                self.testar_http(
                    "https",
                    443,
                )
            )

            if resultado.sucesso:

                print(
                    "HTTPS: acessível"
                )

                print(
                    resultado.resposta
                )

            else:

                print(
                    "HTTPS:",
                    resultado.erro
                )

        print()
        print("=" * 72)
        print(
            "DIAGNÓSTICO CONCLUÍDO"
        )
        print("=" * 72)
        print()

        return {
            "ip":
                self.ip,

            "raw":
                raw_ativo,

            "portas":
                portas,

            "pjl":
                [
                    item.to_dict()
                    for item
                    in self.resultados
                ],
        }


# =========================================================
# TESTE DIRETO
# =========================================================

def main():

    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP não informado."
        )

        return

    probe = PrinterProbe(
        ip
    )

    probe.executar()


if __name__ == "__main__":

    main()