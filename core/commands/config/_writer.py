"""
Printer Assistant - PJL Configuration Writer

Motor genérico para leitura e escrita de configurações PJL.

Operações suportadas:
    INQUIRE  -> configuração corrente
    DINQUIRE -> configuração default
    SET      -> ambiente corrente
    DEFAULT  -> configuração default/persistente

Não assume variáveis específicas da impressora.
"""

import re
import socket
import time


class PJLWriter:
    def __init__(self, ip, port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None

    # ==========================================================
    # CONEXÃO
    # ==========================================================

    def conectar(self):
        if self.sock is not None:
            return

        self.sock = socket.create_connection(
            (self.ip, self.port),
            timeout=self.timeout,
        )

        self.sock.settimeout(self.timeout)

    def fechar(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass

            self.sock = None

    # ==========================================================
    # COMUNICAÇÃO
    # ==========================================================

    def enviar(self, comando, espera=0.15):
        """
        Envia um comando PJL e tenta capturar uma resposta.

        Algumas operações PJL não retornam dados.
        Nesse caso retorna string vazia.
        """

        self.conectar()

        if not comando.endswith("\r\n"):
            comando += "\r\n"

        dados = comando.encode("ascii", errors="replace")

        self.sock.sendall(dados)

        if espera:
            time.sleep(espera)

        resposta = bytearray()

        while True:
            try:
                bloco = self.sock.recv(4096)

                if not bloco:
                    break

                resposta.extend(bloco)

                if len(bloco) < 4096:
                    break

            except socket.timeout:
                break

        return resposta.decode(
            "latin-1",
            errors="replace",
        )

    # ==========================================================
    # CONSULTAS
    # ==========================================================

    def inquire(self, variavel):
        comando = f"@PJL INQUIRE {variavel}"
        resposta = self.enviar(comando)

        return self._extrair_valor(
            resposta,
            variavel,
        )

    def dinquire(self, variavel):
        comando = f"@PJL DINQUIRE {variavel}"
        resposta = self.enviar(comando)

        return self._extrair_valor(
            resposta,
            variavel,
        )

    # ==========================================================
    # ESCRITA
    # ==========================================================

    def set(self, variavel, valor):
        comando = f"@PJL SET {variavel}={valor}"
        return self.enviar(comando)

    def default(self, variavel, valor):
        comando = f"@PJL DEFAULT {variavel}={valor}"
        return self.enviar(comando)

    # ==========================================================
    # VERIFICAÇÃO
    # ==========================================================

    def verificar(self, variavel, esperado):
        """
        Verifica simultaneamente INQUIRE e DINQUIRE.
        """

        corrente = self.inquire(variavel)
        padrao = self.dinquire(variavel)

        return {
            "corrente": corrente,
            "default": padrao,
            "esperado": str(esperado),
            "corrente_ok": str(corrente).upper() == str(esperado).upper(),
            "default_ok": str(padrao).upper() == str(esperado).upper(),
        }

    # ==========================================================
    # PARSER DA RESPOSTA
    # ==========================================================

    @staticmethod
    def _extrair_valor(resposta, variavel):
        if not resposta:
            return None

        linhas = resposta.splitlines()

        alvo = variavel.strip().upper()

        for indice, linha in enumerate(linhas):

            linha_limpa = linha.strip()

            if not linha_limpa:
                continue

            # Remove eventual eco:
            # @PJL INQUIRE DENSITY
            # @PJL DINQUIRE DENSITY
            if linha_limpa.upper().startswith("@PJL"):
                continue

            # Algumas impressoras podem devolver:
            #
            # DENSITY=3
            #
            # ou simplesmente:
            #
            # 3

            if "=" in linha_limpa:
                nome, valor = linha_limpa.split(
                    "=",
                    1,
                )

                if nome.strip().upper() == alvo:
                    return valor.strip().strip('"')

            # Se chegamos aqui, o valor pode ser
            # simplesmente a linha seguinte ao comando.
            #
            # Como já removemos o eco PJL, tentamos
            # interpretar a primeira linha útil.

            return linha_limpa.strip('"')

        return None