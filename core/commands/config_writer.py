"""
Printer Assistant - PJL Configuration Writer

Motor genérico para comunicação e escrita de configurações PJL.

Operações:
    INQUIRE  -> configuração corrente
    DINQUIRE -> configuração default
    SET      -> ambiente corrente
    DEFAULT  -> configuração default/persistente

Não assume variáveis específicas da impressora.
"""

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

        Comandos SET/DEFAULT normalmente não retornam dados.
        INQUIRE/DINQUIRE normalmente retornam o valor solicitado.
        """

        self.conectar()

        if not comando.endswith("\r\n"):
            comando += "\r\n"

        dados = comando.encode(
            "ascii",
            errors="replace",
        )

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

    def inquire_raw(self, variavel):
        """
        Retorna a resposta bruta de INQUIRE.
        """

        comando = f"@PJL INQUIRE {variavel}"

        return self.enviar(comando)

    def dinquire_raw(self, variavel):
        """
        Retorna a resposta bruta de DINQUIRE.
        """

        comando = f"@PJL DINQUIRE {variavel}"

        return self.enviar(comando)

    def inquire(self, variavel):
        """
        Consulta a configuração corrente.
        """

        resposta = self.inquire_raw(variavel)

        return self._extrair_valor(
            resposta,
            variavel,
        )

    def dinquire(self, variavel):
        """
        Consulta a configuração default.
        """

        resposta = self.dinquire_raw(variavel)

        return self._extrair_valor(
            resposta,
            variavel,
        )

    # ==========================================================
    # ESCRITA
    # ==========================================================

    def set(self, variavel, valor):
        """
        Altera o ambiente/configuração corrente.
        """

        comando = f"@PJL SET {variavel}={valor}"

        return self.enviar(comando)

    def default(self, variavel, valor):
        """
        Altera a configuração default/persistente.
        """

        comando = f"@PJL DEFAULT {variavel}={valor}"

        return self.enviar(comando)

    # ==========================================================
    # VERIFICAÇÃO
    # ==========================================================

    def verificar(self, variavel, esperado):
        """
        Consulta INQUIRE e DINQUIRE e compara com o esperado.
        """

        corrente = self.inquire(variavel)
        padrao = self.dinquire(variavel)

        esperado = str(esperado)

        return {
            "corrente": corrente,
            "default": padrao,
            "esperado": esperado,
            "corrente_ok": (
                str(corrente).upper()
                == esperado.upper()
            ),
            "default_ok": (
                str(padrao).upper()
                == esperado.upper()
            ),
        }

    # ==========================================================
    # PARSER DE RESPOSTA
    # ==========================================================

    @staticmethod
    def _extrair_valor(resposta, variavel):
        """
        Extrai o valor de respostas como:

            @PJL INQUIRE DENSITY
            3

        ou:

            DENSITY=3

        ou:

            @PJL DINQUIRE LANG
            PORTUGUESE
        """

        if not resposta:
            return None

        linhas = resposta.splitlines()

        alvo = variavel.strip().upper()

        for linha in linhas:

            linha_limpa = linha.strip()

            if not linha_limpa:
                continue

            # Ignora eco do comando PJL.
            if linha_limpa.upper().startswith("@PJL"):
                continue

            # Formato:
            # DENSITY=3
            if "=" in linha_limpa:

                nome, valor = linha_limpa.split(
                    "=",
                    1,
                )

                if nome.strip().upper() == alvo:
                    return valor.strip().strip('"')

            # Formato:
            # 3
            #
            # ou:
            #
            # ENGLISH
            return linha_limpa.strip('"')

        return None