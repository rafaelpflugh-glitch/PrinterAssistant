"""
Printer Assistant - PJL Capability Discovery

Descobre aquilo que a impressora declara através de:

    @PJL INFO ID
    @PJL INFO CONFIG
    @PJL INFO VARIABLES

Esta etapa NÃO altera configurações.

Objetivo:

    impressora
        ↓
    PJL INFO
        ↓
    parser
        ↓
    mapa de capacidades
        ↓
    interface genérica futura
"""

import re
from typing import Optional

from core.commands.config_writer import PJLWriter
from core.commands.config._capabilities import (
    PJLCapabilities,
    PJLVariable,
)


class PJLCapabilityDiscovery:

    def __init__(
        self,
        ip: str,
        porta: int = 9100,
        timeout: int = 5,
    ):
        self.ip = ip
        self.porta = porta
        self.timeout = timeout

        self.writer = PJLWriter(
            ip,
            port=porta,
            timeout=timeout,
        )

    # ==========================================================
    # CONEXÃO
    # ==========================================================

    def conectar(self):
        self.writer.conectar()

    def fechar(self):
        self.writer.fechar()

    # ==========================================================
    # ENVIO PJL
    # ==========================================================

    def _info(self, consulta: str) -> str:
        comando = f"@PJL INFO {consulta}"

        return self.writer.enviar(
            comando,
            espera=0.2,
        )

    # ==========================================================
    # ID
    # ==========================================================

    def descobrir_id(self):
        resposta = self._info("ID")

        modelo = None

        for linha in resposta.splitlines():

            linha = linha.strip()

            if not linha:
                continue

            if linha.upper().startswith("@PJL"):
                continue

            if linha.startswith('"') and linha.endswith('"'):
                modelo = linha.strip('"')
                break

            modelo = linha
            break

        return modelo

    # ==========================================================
    # CONFIG
    # ==========================================================

    def descobrir_config(self):
        return self._info("CONFIG")

    # ==========================================================
    # VARIABLES
    # ==========================================================

    def descobrir_variables_raw(self):
        return self._info("VARIABLES")

    # ==========================================================
    # FAMÍLIA
    # ==========================================================

    @staticmethod
    def _familia(nome: str) -> str:

        nome_upper = nome.upper()

        if "PCL" in nome_upper:
            return "PCL"

        if "POSTSCRIPT" in nome_upper:
            return "POSTSCRIPT"

        if (
            "TRAY" in nome_upper
            or "FEEDER" in nome_upper
            or "PAPER" in nome_upper
            or "MEDIA" in nome_upper
            or "ENVELOPE" in nome_upper
        ):
            return "MIDIA/BANDEJAS"

        if (
            "IMAGE" in nome_upper
            or "COLOR" in nome_upper
            or "BRIGHTNESS" in nome_upper
            or "CONTRAST" in nome_upper
        ):
            return "IMAGEM"

        if (
            "POWER" in nome_upper
            or "HIBERNATE" in nome_upper
            or "QUIET" in nome_upper
            or "ENERGY" in nome_upper
        ):
            return "ENERGIA"

        if "FAX" in nome_upper:
            return "FAX"

        if "IPP" in nome_upper:
            return "IPP"

        return "GERAL"

    # ==========================================================
    # PARSER
    # ==========================================================

    def parse_variables(
        self,
        texto: str,
    ) -> PJLCapabilities:

        capabilities = PJLCapabilities()

        linhas = texto.splitlines()

        indice = 0

        while indice < len(linhas):

            linha = linhas[indice].strip()

            if not linha:
                indice += 1
                continue

            # Ignora cabeçalho
            if linha.upper().startswith("@PJL"):
                indice += 1
                continue

            # --------------------------------------------------
            # VARIÁVEL
            #
            # Exemplo:
            #
            # DENSITY=3 [2 RANGE]
            #
            # LANG=PORTUGUESE [21 ENUMERATED]
            #
            # PASSWORD=DISABLED [2 RANGE]
            # --------------------------------------------------

            match = re.match(
                r'^([^\s=]+(?:\\:[^\s=]+)*)'
                r'=(.*?)'
                r'\s+\[(.*?)\]\s*$',
                linha,
            )

            if not match:
                indice += 1
                continue

            nome = match.group(1).strip()

            valor = match.group(2).strip()

            descriptor = match.group(3).strip()

            descriptor_upper = descriptor.upper()

            variavel = PJLVariable(
                nome=nome,
                valor=valor,
                familia=self._familia(nome),
            )

            # --------------------------------------------------
            # TIPO
            # --------------------------------------------------

            if "ENUMERATED" in descriptor_upper:
                variavel.tipo = "ENUMERATED"

            elif "RANGE" in descriptor_upper:
                variavel.tipo = "RANGE"

            elif "QUOTED STRING" in descriptor_upper:
                variavel.tipo = "QUOTED STRING"

            else:
                variavel.tipo = descriptor

            # --------------------------------------------------
            # READONLY
            # --------------------------------------------------

            if "READONLY" in descriptor_upper:
                variavel.readonly = True

            # --------------------------------------------------
            # LINHAS SEGUINTES
            #
            # ENUMERATED:
            #
            # LANG=PORTUGUESE [21 ENUMERATED]
            #     ENGLISH
            #     FRENCH
            #     ...
            #
            # RANGE:
            #
            # DENSITY=3 [2 RANGE]
            #     1
            #     5
            # --------------------------------------------------

            valores = []

            proximo = indice + 1

            while proximo < len(linhas):

                candidata = linhas[proximo]

                if not candidata.strip():
                    proximo += 1
                    continue

                # Se começa sem indentação, provavelmente
                # é uma nova variável.
                if candidata[0] not in (" ", "\t"):
                    break

                conteudo = candidata.strip()

                # Não aceitar linhas PJL.
                if conteudo.upper().startswith("@PJL"):
                    break

                # --------------------------------------------------
                # RANGE
                # --------------------------------------------------

                if (
                    variavel.tipo == "RANGE"
                    and not variavel.valores
                ):
                    numero = conteudo

                    if self._parece_numero(numero):

                        if variavel.minimo is None:
                            variavel.minimo = numero

                        elif variavel.maximo is None:
                            variavel.maximo = numero

                        else:
                            break

                        proximo += 1
                        continue

                # --------------------------------------------------
                # ENUMERATED
                # --------------------------------------------------

                if variavel.tipo == "ENUMERATED":

                    # Uma enumeração é normalmente uma linha
                    # simples sem espaços internos significativos.
                    valores.append(
                        conteudo.strip('"')
                    )

                    proximo += 1
                    continue

                proximo += 1

            variavel.valores = valores

            capabilities.adicionar(
                variavel
            )

            indice = proximo

        return capabilities

    # ==========================================================
    # UTIL
    # ==========================================================

    @staticmethod
    def _parece_numero(valor: str) -> bool:

        return bool(
            re.fullmatch(
                r'-?\d+(?:\.\d+)?',
                valor.strip(),
            )
        )

    # ==========================================================
    # DESCOBERTA COMPLETA
    # ==========================================================

    def descobrir(self):

        capabilities = PJLCapabilities()

        # ------------------------------------------------------
        # ID
        # ------------------------------------------------------

        capabilities.modelo = self.descobrir_id()

        # ------------------------------------------------------
        # VARIABLES
        # ------------------------------------------------------

        raw_variables = self.descobrir_variables_raw()

        parsed = self.parse_variables(
            raw_variables
        )

        capabilities.variaveis = (
            parsed.variaveis
        )

        # ------------------------------------------------------
        # CONFIG
        # ------------------------------------------------------

        config = self.descobrir_config()

        self._extrair_metadados_config(
            capabilities,
            config,
        )

        return capabilities

    # ==========================================================
    # METADADOS CONFIG
    # ==========================================================

    @staticmethod
    def _extrair_metadados_config(
        capabilities: PJLCapabilities,
        texto: str,
    ):

        for linha in texto.splitlines():

            linha = linha.strip()

            if not linha:
                continue

            upper = linha.upper()

            if upper.startswith(
                "SYSTEM FIRMWARE VERSION="
            ):
                capabilities.firmware = (
                    linha.split("=", 1)[1].strip()
                )

            elif upper.startswith(
                "SERIAL NUMBER="
            ):
                capabilities.serial = (
                    linha.split("=", 1)[1].strip()
                )