
"""
PRINTER ASSISTANT

RELATORIO DE CONFIGURACAO E SUPRIMENTOS

Este relatorio representa uma fotografia tecnica da impressora
no momento em que o equipamento esta pronto para ser embalado
e enviado ao cliente.

Responsabilidades:

- receber um PrinterDevice ja coletado;
- utilizar somente os dados existentes no dispositivo;
- organizar as informacoes tecnicas da impressora;
- apresentar os suprimentos instalados;
- gerar PCL;
- enviar o relatorio para a impressora pela porta RAW 9100.

IMPORTANTE:

Este modulo NAO realiza nova coleta da impressora.

A coleta PJL + SYSDEBUG + SNMP deve ter sido realizada
anteriormente pelo PrinterDevice.

Fluxo:

PrinterDevice
    |
    v
ConfiguracaoReport
    |
    v
gerar_linhas()
    |
    v
gerar_pcl()
    |
    v
imprimir()
    |
    v
Lexmark :9100
"""

from __future__ import annotations

import socket


# ============================================================
# CONFIGURACAO
# ============================================================

PORTA_RAW = 9100


# ============================================================
# EXCECAO
# ============================================================

class ConfiguracaoReportError(Exception):
    """
    Erro controlado durante a geracao ou impressao
    do relatorio de configuracao e suprimentos.
    """

    pass


# ============================================================
# CLASSE PRINCIPAL
# ============================================================

class ConfiguracaoReport:

    # ========================================================
    # INICIALIZACAO
    # ========================================================

    def __init__(self, device):

        if device is None:
            raise ConfiguracaoReportError(
                "Nenhuma impressora esta selecionada."
            )

        self.device = device

    # ========================================================
    # DADOS
    # ========================================================

    def _dados(self):

        try:
            dados = self.device.to_dict()

        except Exception as erro:
            raise ConfiguracaoReportError(
                "Nao foi possivel acessar os dados "
                "do PrinterDevice."
            ) from erro

        if not isinstance(dados, dict):
            raise ConfiguracaoReportError(
                "PrinterDevice.to_dict() nao retornou "
                "um dicionario valido."
            )

        return dados

    # ========================================================
    # FORMATACAO DE TEXTO
    # ========================================================

    @staticmethod
    def _texto(valor, padrao="N/D"):

        if valor is None:
            return padrao

        valor = str(valor).strip()

        if not valor:
            return padrao

        return valor

    # ========================================================
    # FORMATACAO NUMERICA
    # ========================================================

    @staticmethod
    def _numero(valor, padrao="N/D"):

        if valor is None:
            return padrao

        try:
            return (
                f"{int(float(valor)):,}"
                .replace(",", ".")
            )

        except (TypeError, ValueError):
            return ConfiguracaoReport._texto(
                valor,
                padrao,
            )

    # ========================================================
    # PERCENTUAL
    # ========================================================

    @staticmethod
    def _percentual(valor):

        if valor is None:
            return "N/D"

        try:
            numero = float(valor)

            if numero.is_integer():
                return f"{int(numero)} %"

            return f"{numero:.1f} %"

        except (TypeError, ValueError):
            return ConfiguracaoReport._texto(valor)

    # ========================================================
    # BARRA GRAFICA
    # ========================================================

    @staticmethod
    def _barra(valor, largura=28):

        try:
            percentual = float(valor)

        except (TypeError, ValueError):
            return (
                "["
                + ("-" * largura)
                + "]"
            )

        percentual = max(
            0,
            min(
                100,
                percentual,
            ),
        )

        preenchido = round(
            largura * percentual / 100
        )

        vazio = largura - preenchido

        return (
            "["
            + ("#" * preenchido)
            + ("-" * vazio)
            + "]"
        )

    # ========================================================
    # CONDICAO DO SUPRIMENTO
    # ========================================================

    @staticmethod
    def _condicao(supply):

        if not isinstance(supply, dict):
            return "N/D"

        condicao = supply.get("condicao")

        if condicao is None:
            return "N/D"

        condicao = str(condicao).strip()

        if not condicao:
            return "N/D"

        return condicao.upper()

    # ========================================================
    # TIPO DO SUPRIMENTO
    # ========================================================

    @staticmethod
    def _tipo(supply):

        if not isinstance(supply, dict):
            return "SUPRIMENTO"

        tipo = supply.get("tipo")

        if not tipo:
            return "SUPRIMENTO"

        tipo = str(tipo).strip().lower()

        tipos = {
            "toner": "TONER",
            "cartucho": "TONER",
            "cartridge": "TONER",

            "unidade_imagem": "UNIDADE DE IMAGEM",
            "unidade imagem": "UNIDADE DE IMAGEM",
            "imaging": "UNIDADE DE IMAGEM",
            "imaging unit": "UNIDADE DE IMAGEM",
            "photoconductor": "UNIDADE DE IMAGEM",
            "drum": "UNIDADE DE IMAGEM",

            "fusor": "FUSOR",
            "fuser": "FUSOR",

            "maintenance": "KIT DE MANUTENCAO",
            "maintenance kit": "KIT DE MANUTENCAO",
        }

        return tipos.get(
            tipo,
            str(tipo).upper(),
        )

    # ========================================================
    # NOME DO SUPRIMENTO
    # ========================================================

    def _nome_supply(self, supply, numero):

        tipo = self._tipo(supply)

        nome = (
            supply.get("nome")
            or supply.get("name")
            or supply.get("descricao")
            or supply.get("description")
        )

        if nome:
            nome = str(nome).strip()

            if nome:
                return nome.upper()

        return tipo

    # ========================================================
    # LINHAS DO SUPRIMENTO
    # ========================================================

    def _linhas_supply(self, supply, numero):

        linhas = []

        nome = self._nome_supply(
            supply,
            numero,
        )

        tipo = self._tipo(supply)

        nivel = supply.get("nivel")

        if nivel is None:
            nivel = supply.get("percentual")

        capacidade = supply.get("capacidade")
        restante = supply.get("restante")
        consumido = supply.get("consumido")

        condicao = self._condicao(
            supply
        )

        serial = (
            supply.get("numero_serie")
            or supply.get("serial")
        )

        # ----------------------------------------------------
        # CABECALHO DO SUPRIMENTO
        # ----------------------------------------------------

        linhas.append(
            f"SUPRIMENTO {numero:02d}"
        )

        linhas.append(
            f"    {nome}"
        )

        # ----------------------------------------------------
        # NIVEL
        # ----------------------------------------------------

        linhas.append(
            f"    Nivel:        "
            f"{self._percentual(nivel)}"
        )

        linhas.append(
            f"    {self._barra(nivel)}"
        )

        # ----------------------------------------------------
        # QUANTIDADES
        # ----------------------------------------------------

        linhas.append(
            f"    Capacidade:   "
            f"{self._numero(capacidade)}"
        )

        linhas.append(
            f"    Restante:     "
            f"{self._numero(restante)}"
        )

        linhas.append(
            f"    Consumido:    "
            f"{self._numero(consumido)}"
        )

        # ----------------------------------------------------
        # CONDICAO
        # ----------------------------------------------------

        linhas.append(
            f"    Condicao:     "
            f"{condicao}"
        )

        # ----------------------------------------------------
        # NUMERO DE SERIE
        # ----------------------------------------------------

        if tipo not in (
            "FUSOR",
            "KIT DE MANUTENCAO",
        ):

            if serial:
                linhas.append(
                    "    Numero serie: "
                    + str(serial)
                )

        return linhas

    # ========================================================
    # GERAR LINHAS
    # ========================================================

    def gerar_linhas(self):

        dados = self._dados()

        identificacao = dados.get(
            "identificacao",
            {},
        )

        if not isinstance(
            identificacao,
            dict,
        ):
            identificacao = {}

        linhas = []

        # ====================================================
        # CABECALHO
        # ====================================================

        linhas.append(
            "PRINTER ASSISTANT"
        )

        linhas.append(
            "RELATORIO TECNICO"
        )

        linhas.append(
            "CONFIGURACAO E SUPRIMENTOS"
        )

        linhas.append(
            "========================================"
        )

        linhas.append("")

        # ====================================================
        # IDENTIFICACAO DA IMPRESSORA
        # ====================================================

        linhas.append(
            "IDENTIFICACAO DA IMPRESSORA"
        )

        linhas.append(
            "----------------------------------------"
        )

        linhas.append(
            "Fabricante:    "
            + self._texto(
                identificacao.get(
                    "fabricante"
                ),
                "Lexmark",
            )
        )

        linhas.append(
            "Modelo:        "
            + self._texto(
                identificacao.get(
                    "modelo"
                )
            )
        )

        linhas.append(
            "Familia:       "
            + self._texto(
                identificacao.get(
                    "familia"
                )
            )
        )

        linhas.append(
            "Tipo:          "
            + self._texto(
                identificacao.get(
                    "tipo"
                )
            )
        )

        linhas.append(
            "Numero serie:  "
            + self._texto(
                identificacao.get(
                    "serial"
                )
            )
        )

        linhas.append(
            "Firmware:      "
            + self._texto(
                identificacao.get(
                    "firmware"
                )
            )
        )

        linhas.append(
            "Contador:      "
            + self._numero(
                identificacao.get(
                    "contador"
                )
            )
        )

        ip = (
            dados.get("ip")
            or getattr(
                self.device,
                "ip",
                None,
            )
        )

        linhas.append(
            "Endereco IP:   "
            + self._texto(ip)
        )

        # Espaco visual antes dos suprimentos
        linhas.append("")
        linhas.append("")
        linhas.append("")

        # ====================================================
        # SUPRIMENTOS
        # ====================================================

        linhas.append(
            "SUPRIMENTOS INSTALADOS"
        )

        linhas.append(
            "----------------------------------------"
        )

        supplies = dados.get(
            "supplies",
            [],
        )

        if not isinstance(
            supplies,
            list,
        ):
            supplies = []

        if not supplies:

            linhas.append(
                "Nenhum suprimento encontrado."
            )

        else:

            numero = 0

            for supply in supplies:

                if not isinstance(
                    supply,
                    dict,
                ):
                    continue

                numero += 1

                linhas.extend(
                    self._linhas_supply(
                        supply,
                        numero,
                    )
                )

                # Espaco maior entre suprimentos
                linhas.append("")
                linhas.append("")

        # ====================================================
        # RODAPE
        # ====================================================

        linhas.append("")

        linhas.append(
            "========================================"
        )

        linhas.append(
            "Relatorio gerado pelo Printer Assistant."
        )

        return linhas

    # ========================================================
    # GERAR PCL
    # ========================================================

    def gerar_pcl(self):

        ESC = b"\x1b"

        linhas = self.gerar_linhas()

        dados = bytearray()

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------

        dados += (
            ESC
            + b"E"
        )

        # ----------------------------------------------------
        # PAPEL A4
        # ----------------------------------------------------

        dados += (
            ESC
            + b"&l26A"
        )

        # ----------------------------------------------------
        # RETRATO
        # ----------------------------------------------------

        dados += (
            ESC
            + b"&l0O"
        )

        # ----------------------------------------------------
        # MARGEM
        # ----------------------------------------------------

        dados += (
            ESC
            + b"&a5L"
        )

        # ----------------------------------------------------
        # ESPACAMENTO VERTICAL
        #
        # 6D = aproximadamente 6 linhas por polegada.
        #
        # O relatorio anterior utilizava 8D.
        # 6D deixa o documento mais aberto e confortavel
        # para leitura em uma folha A4.
        # ----------------------------------------------------

        dados += (
            ESC
            + b"&l6D"
        )

        # ----------------------------------------------------
        # FONTE
        # ----------------------------------------------------

        fonte = (
            ESC
            + b"(s0p10h0s0b19U"
        )

        dados += fonte

        # ----------------------------------------------------
        # TEXTO
        # ----------------------------------------------------

        for linha in linhas:

            dados += fonte

            linha_bytes = (
                str(linha)
                .encode(
                    "cp1252",
                    errors="replace",
                )
            )

            dados += linha_bytes

            dados += b"\r\n"

        # ----------------------------------------------------
        # FORM FEED
        # ----------------------------------------------------

        dados += b"\x0c"

        # ----------------------------------------------------
        # FIM DO JOB
        # ----------------------------------------------------

        dados += (
            b"\x1b%-12345X"
        )

        return bytes(dados)

    # ========================================================
    # IMPRESSAO
    # ========================================================

    def imprimir(self):

        dados = self._dados()

        ip = (
            dados.get("ip")
            or getattr(
                self.device,
                "ip",
                None,
            )
        )

        if not ip:
            raise ConfiguracaoReportError(
                "A impressora selecionada nao possui "
                "endereco IP."
            )

        pcl = self.gerar_pcl()

        if not pcl:
            raise ConfiguracaoReportError(
                "O relatorio PCL foi gerado vazio."
            )

        try:

            with socket.create_connection(
                (
                    ip,
                    PORTA_RAW,
                ),
                timeout=10,
            ) as sock:

                sock.sendall(pcl)

        except OSError as erro:

            raise ConfiguracaoReportError(
                "Nao foi possivel enviar o "
                "Relatorio de Configuracao e "
                "Suprimentos.\n\n"
                f"Destino: {ip}:{PORTA_RAW}\n\n"
                f"{erro}"
            ) from erro

        return {
            "sucesso": True,
            "relatorio": "configuracao",
            "tipo": "configuracao_e_suprimentos",
            "ip": ip,
            "porta": PORTA_RAW,
            "bytes": len(pcl),
            "linhas": len(
                self.gerar_linhas()
            ),
        }


# ============================================================
# FUNCAO PUBLICA
# ============================================================

def imprimir_relatorio_configuracao(device):

    relatorio = ConfiguracaoReport(
        device
    )

    return relatorio.imprimir()


# ============================================================
# FIM
# ============================================================


