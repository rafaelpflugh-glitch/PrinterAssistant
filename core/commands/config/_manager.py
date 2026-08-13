"""
Printer Assistant - PJL Configuration Manager

Camada de alto nível para leitura, escrita e restauração
de configurações PJL.

Fluxo:

    _parser  -> interpreta INFO VARIABLES
    config_writer -> comunica via RAW/PJL
    _manager -> coordena leitura/escrita/verificação

Operações:

    INQUIRE  -> configuração corrente
    DINQUIRE -> configuração default
    SET      -> ambiente corrente
    DEFAULT  -> configuração persistente
"""

from core.commands.config_writer import PJLWriter
from core.commands.config._parser import PJLConfigParser


class PJLConfigManager:

    def __init__(
        self,
        ip,
        porta=9100,
        timeout=5,
    ):
        self.ip = ip
        self.porta = porta
        self.timeout = timeout

        self.writer = PJLWriter(
            ip=ip,
            port=porta,
            timeout=timeout,
        )

        self.parser = PJLConfigParser()

    # ==========================================================
    # CONEXÃO
    # ==========================================================

    def conectar(self):
        self.writer.conectar()

    def fechar(self):
        self.writer.fechar()

    # ==========================================================
    # LEITURA
    # ==========================================================

    def inquire(self, variavel):
        """
        Lê a configuração corrente.
        """

        return self.writer.inquire(variavel)

    def dinquire(self, variavel):
        """
        Lê a configuração default.
        """

        return self.writer.dinquire(variavel)

    # ==========================================================
    # ESCRITA
    # ==========================================================

    def set(self, variavel, valor):
        """
        Altera o ambiente corrente.
        """

        return self.writer.set(
            variavel,
            valor,
        )

    def default(self, variavel, valor):
        """
        Altera a configuração default/persistente.
        """

        return self.writer.default(
            variavel,
            valor,
        )

    # ==========================================================
    # ESTADO
    # ==========================================================

    def estado(self, variavel):
        """
        Retorna corrente + default.
        """

        return {
            "variavel": variavel,
            "corrente": self.inquire(variavel),
            "default": self.dinquire(variavel),
        }

    # ==========================================================
    # ALTERAÇÃO PERSISTENTE
    # ==========================================================

    def alterar_default(
        self,
        variavel,
        valor,
        verificar=True,
    ):
        """
        Altera o default e opcionalmente verifica
        INQUIRE + DINQUIRE.
        """

        resposta = self.default(
            variavel,
            valor,
        )

        resultado = {
            "variavel": variavel,
            "valor_solicitado": str(valor),
            "resposta": resposta,
        }

        if verificar:
            corrente = self.inquire(variavel)
            padrao = self.dinquire(variavel)

            resultado.update({
                "corrente": corrente,
                "default": padrao,
                "corrente_ok": (
                    str(corrente).upper()
                    == str(valor).upper()
                ),
                "default_ok": (
                    str(padrao).upper()
                    == str(valor).upper()
                ),
            })

        return resultado

    # ==========================================================
    # RESTAURAÇÃO
    # ==========================================================

    def restaurar_default(
        self,
        variavel,
        valor_original,
    ):
        """
        Restaura o default original.
        """

        resposta = self.default(
            variavel,
            valor_original,
        )

        corrente = self.inquire(variavel)
        padrao = self.dinquire(variavel)

        return {
            "variavel": variavel,
            "valor_original": str(valor_original),
            "corrente": corrente,
            "default": padrao,
            "restaurado": (
                str(padrao).upper()
                == str(valor_original).upper()
            ),
            "resposta": resposta,
        }

    # ==========================================================
    # TESTE CONTROLADO
    # ==========================================================

    def probe_default(
        self,
        variavel,
        valor_teste,
        valor_restauracao=None,
    ):
        """
        Executa:

            DINQUIRE
            INQUIRE

            DEFAULT valor_teste

            INQUIRE
            DINQUIRE

            DEFAULT valor_original

            INQUIRE
            DINQUIRE

        """

        original_default = self.dinquire(
            variavel
        )

        original_corrente = self.inquire(
            variavel
        )

        if valor_restauracao is None:
            valor_restauracao = original_default

        resultado = {
            "variavel": variavel,
            "original_default": original_default,
            "original_corrente": original_corrente,
        }

        try:

            self.default(
                variavel,
                valor_teste,
            )

            resultado["apos_default"] = {
                "corrente": self.inquire(
                    variavel
                ),
                "default": self.dinquire(
                    variavel
                ),
            }

        finally:

            self.default(
                variavel,
                valor_restauracao,
            )

            resultado["final"] = {
                "corrente": self.inquire(
                    variavel
                ),
                "default": self.dinquire(
                    variavel
                ),
            }

        return resultado