"""
============================================================
PRINTER ASSISTANT
DEMONSTRATION REPORT SERVICE
============================================================

Relatório de Demonstração / Página de Qualidade.

Responsabilidades:

- utilizar a imagem oficial fornecida pelo usuário;
- gerar um PDF de uma única página;
- preparar a mesma imagem para impressão PCL raster;
- imprimir diretamente na UST através de RAW 9100;
- não realizar nova coleta da impressora;
- utilizar o IP do PrinterDevice já coletado.

IMPORTANTE:

Este serviço NÃO modifica:

- coleta;
- PJL;
- SYSDEBUG;
- SNMP;
- identificação;
- suprimentos;
- Relatório de Configuração e Suprimentos;
- Relatório de Ativo.

A imagem utilizada é:

C:\\PrinterAssistant\\assets\\print_too_dark_check_1.jpg

============================================================
"""

from __future__ import annotations

import socket
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz


# ============================================================
# CAMINHOS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IMAGE_PATH = (
    PROJECT_ROOT
    / "assets"
    / "print_too_dark_check_1.jpg"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "demonstracao"
)


# ============================================================
# IMPRESSORA
# ============================================================

PORTA_RAW = 9100

DPI_IMPRESSAO = 600

# Margem física aproximada.
# 0,20" = 144 decipoints.
MARGEM_DE_CIPONTOS = 144


# ============================================================
# ERRO
# ============================================================

class DemonstrationError(Exception):
    """
    Erro específico do relatório de demonstração.
    """

    pass


# ============================================================
# SERVIÇO
# ============================================================

class DemonstrationService:

    def __init__(
        self,
        device=None,
    ):
        self.device = device

        self.ip: Optional[str] = None

        self.pdf_path: Optional[Path] = None

        self.pcl_data: Optional[bytes] = None

        self.preview_png: Optional[bytes] = None

        self._imagem_doc = None

    # ========================================================
    # IP DO DEVICE
    # ========================================================

    def _obter_ip(self) -> str:

        if self.device is None:
            raise DemonstrationError(
                "Nenhuma impressora foi fornecida."
            )

        dados = self.device.to_dict()

        ip = dados.get(
            "ip",
            "",
        )

        if not ip:
            raise DemonstrationError(
                "O endereço IP da impressora "
                "não está disponível."
            )

        return str(ip).strip()

    # ========================================================
    # VALIDAR IMAGEM
    # ========================================================

    @staticmethod
    def _validar_imagem():

        if not IMAGE_PATH.exists():

            raise DemonstrationError(
                "A imagem oficial da demonstração "
                "não foi encontrada.\n\n"
                f"Caminho esperado:\n{IMAGE_PATH}"
            )

        if not IMAGE_PATH.is_file():

            raise DemonstrationError(
                "O caminho da imagem da demonstração "
                "não aponta para um arquivo.\n\n"
                f"{IMAGE_PATH}"
            )

    # ========================================================
    # ABRIR IMAGEM
    # ========================================================

    def _abrir_imagem(self):

        self._validar_imagem()

        try:

            doc = fitz.open(
                str(IMAGE_PATH)
            )

        except Exception as erro:

            raise DemonstrationError(
                "Não foi possível abrir a imagem "
                "da demonstração.\n\n"
                f"{erro}"
            ) from erro

        if doc.page_count < 1:

            doc.close()

            raise DemonstrationError(
                "A imagem da demonstração "
                "não possui conteúdo."
            )

        self._imagem_doc = doc

        return doc[0]

    # ========================================================
    # GERAR PDF
    # ========================================================

    def _gerar_pdf(
        self,
        page_imagem,
    ) -> Path:

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        agora = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        caminho_pdf = (
            OUTPUT_DIR
            / f"demonstracao_{agora}.pdf"
        )

        # ----------------------------------------------------
        # A4
        # ----------------------------------------------------

        largura_a4 = 595.276
        altura_a4 = 841.890

        pagina = fitz.open()

        pagina_a4 = pagina.new_page(
            width=largura_a4,
            height=altura_a4,
        )

        # ----------------------------------------------------
        # ÁREA ÚTIL
        # ----------------------------------------------------

        margem = 14.1732
        # aproximadamente 5 mm

        area = fitz.Rect(
            margem,
            margem,
            largura_a4 - margem,
            altura_a4 - margem,
        )

        # ----------------------------------------------------
        # INSERÇÃO DA IMAGEM
        # ----------------------------------------------------

        pagina_a4.insert_image(
            area,
            filename=str(
                IMAGE_PATH
            ),
            keep_proportion=True,
            overlay=True,
        )

        # ----------------------------------------------------
        # SALVAR
        # ----------------------------------------------------

        try:

            pagina.save(
                str(caminho_pdf),
                garbage=4,
                deflate=True,
            )

        except Exception as erro:

            pagina.close()

            raise DemonstrationError(
                "Não foi possível gerar o PDF "
                "da demonstração.\n\n"
                f"{erro}"
            ) from erro

        pagina.close()

        return caminho_pdf

    # ========================================================
    # RENDERIZAR IMAGEM PARA IMPRESSÃO
    # ========================================================

    def _renderizar_para_pcl(
        self,
        page_imagem,
    ):

        """
        Renderiza a imagem em escala apropriada para
        impressão monocromática PCL.

        A imagem é ajustada para A4 com margem.

        A resolução utilizada é 600 DPI.
        """

        # ----------------------------------------------------
        # DIMENSÕES A4 EM POLEGADAS
        # ----------------------------------------------------

        a4_largura = 8.27
        a4_altura = 11.69

        margem = (
            MARGEM_DE_CIPONTOS
            / 720.0
        )

        largura_util = (
            a4_largura
            - (margem * 2)
        )

        altura_util = (
            a4_altura
            - (margem * 2)
        )

        # ----------------------------------------------------
        # DIMENSÕES ORIGINAIS
        # ----------------------------------------------------

        origem_largura = page_imagem.rect.width
        origem_altura = page_imagem.rect.height

        if origem_largura <= 0:
            raise DemonstrationError(
                "A largura da imagem é inválida."
            )

        if origem_altura <= 0:
            raise DemonstrationError(
                "A altura da imagem é inválida."
            )

        proporcao = min(
            largura_util / (
                origem_largura / 72.0
            ),
            altura_util / (
                origem_altura / 72.0
            ),
        )

        largura_px = max(
            1,
            int(
                origem_largura
                * proporcao
                / 72.0
                * DPI_IMPRESSAO
            ),
        )

        altura_px = max(
            1,
            int(
                origem_altura
                * proporcao
                / 72.0
                * DPI_IMPRESSAO
            ),
        )

        # ----------------------------------------------------
        # ESCALA DIRETA PARA O TAMANHO FINAL
        # ----------------------------------------------------

        escala_x = (
            largura_px
            / origem_largura
        )

        escala_y = (
            altura_px
            / origem_altura
        )

        escala = min(
            escala_x,
            escala_y,
        )

        pixmap = page_imagem.get_pixmap(
            matrix=fitz.Matrix(
                escala,
                escala,
            ),
            colorspace=fitz.csGRAY,
            alpha=False,
        )

        return pixmap

    # ========================================================
    # CONVERTER PARA 1 BIT
    # ========================================================

    @staticmethod
    def _converter_1bit(
        pixmap,
    ):

        """
        Converte a imagem grayscale para 1 bit.

        Preto = 1
        Branco = 0

        É utilizada uma matriz Bayer 4x4 para preservar
        melhor os tons intermediários na impressão.
        """

        largura = pixmap.width
        altura = pixmap.height

        samples = pixmap.samples

        matriz = (
            (0, 8, 2, 10),
            (12, 4, 14, 6),
            (3, 11, 1, 9),
            (15, 7, 13, 5),
        )

        saida = []

        bytes_por_linha = (
            (largura + 7)
            // 8
        )

        for y in range(altura):

            linha = bytearray(
                bytes_por_linha
            )

            offset = (
                y
                * largura
            )

            for x in range(largura):

                cinza = samples[
                    offset + x
                ]

                limite = (
                    matriz[
                        y % 4
                    ][
                        x % 4
                    ]
                    * 16
                    + 8
                )

                # Preto = 1
                if cinza < limite:

                    indice = x // 8

                    bit = 7 - (
                        x % 8
                    )

                    linha[indice] |= (
                        1 << bit
                    )

            saida.append(
                bytes(linha)
            )

        return (
            largura,
            altura,
            saida,
        )

    # ========================================================
    # RUN LENGTH PCL
    # ========================================================

    @staticmethod
    def _rle_pcl(
        dados: bytes,
    ) -> bytes:

        """
        Compression Method 1 do PCL.

        Cada par:

            contador
            byte

        O contador representa repetições adicionais.

        Portanto:

            0 = 1 ocorrência
            1 = 2 ocorrências
            ...
            255 = 256 ocorrências
        """

        if not dados:
            return b""

        resultado = bytearray()

        atual = dados[0]

        quantidade = 1

        for byte in dados[1:]:

            if (
                byte == atual
                and quantidade < 256
            ):

                quantidade += 1

            else:

                resultado.append(
                    quantidade - 1
                )

                resultado.append(
                    atual
                )

                atual = byte
                quantidade = 1

        resultado.append(
            quantidade - 1
        )

        resultado.append(
            atual
        )

        return bytes(
            resultado
        )

    # ========================================================
    # GERAR PCL
    # ========================================================

    def _gerar_pcl(
        self,
        page_imagem,
    ) -> bytes:

        pixmap = self._renderizar_para_pcl(
            page_imagem
        )

        (
            largura,
            altura,
            linhas,
        ) = self._converter_1bit(
            pixmap
        )

        # ----------------------------------------------------
        # TAMANHO A4
        # ----------------------------------------------------

        largura_a4_dpi = int(
            8.27
            * DPI_IMPRESSAO
        )

        altura_a4_dpi = int(
            11.69
            * DPI_IMPRESSAO
        )

        # ----------------------------------------------------
        # POSIÇÃO CENTRALIZADA
        # ----------------------------------------------------

        margem_x = max(
            0,
            (
                largura_a4_dpi
                - largura
            ) // 2,
        )

        margem_y = max(
            0,
            (
                altura_a4_dpi
                - altura
            ) // 2,
        )

        # ----------------------------------------------------
        # CONVERSÃO PARA DECIPOINTS
        # ----------------------------------------------------

        x_decipoints = int(
            margem_x
            * 720
            / DPI_IMPRESSAO
        )

        y_decipoints = int(
            margem_y
            * 720
            / DPI_IMPRESSAO
        )

        # ----------------------------------------------------
        # PCL
        # ----------------------------------------------------

        esc = b"\x1b"

        pcl = bytearray()

        # Reset
        pcl += esc + b"E"

        # ----------------------------------------------------
        # PJL
        # ----------------------------------------------------

        pcl += (
            b"@PJL JOB NAME="
            b'"PA_DEMONSTRACAO"\r\n'
        )

        pcl += (
            b"@PJL ENTER LANGUAGE=PCL\r\n"
        )

        # ----------------------------------------------------
        # A4 / RETRATO
        # ----------------------------------------------------

        pcl += (
            esc
            + b"&l26A"
        )

        pcl += (
            esc
            + b"&l0O"
        )

        # ----------------------------------------------------
        # POSIÇÃO
        # ----------------------------------------------------

        pcl += (
            esc
            + f"&a{x_decipoints}H".encode(
                "ascii"
            )
        )

        pcl += (
            esc
            + f"&a{y_decipoints}V".encode(
                "ascii"
            )
        )

        # ----------------------------------------------------
        # RESOLUÇÃO
        # ----------------------------------------------------

        pcl += (
            esc
            + f"*t{DPI_IMPRESSAO}R".encode(
                "ascii"
            )
        )

        # ----------------------------------------------------
        # TAMANHO RASTER
        # ----------------------------------------------------

        pcl += (
            esc
            + f"*r{largura}S".encode(
                "ascii"
            )
        )

        pcl += (
            esc
            + f"*r{altura}T".encode(
                "ascii"
            )
        )

        # ----------------------------------------------------
        # INICIAR GRÁFICOS
        # ----------------------------------------------------

        pcl += (
            esc
            + b"*r1A"
        )

        # ----------------------------------------------------
        # RUN LENGTH
        # ----------------------------------------------------

        pcl += (
            esc
            + b"*b1M"
        )

        # ----------------------------------------------------
        # DADOS
        # ----------------------------------------------------

        for linha in linhas:

            comprimida = (
                DemonstrationService
                ._rle_pcl(
                    linha
                )
            )

            pcl += (
                esc
                + f"*b{len(comprimida)}W".encode(
                    "ascii"
                )
            )

            pcl += comprimida

        # ----------------------------------------------------
        # FINALIZAR GRÁFICOS
        # ----------------------------------------------------

        pcl += (
            esc
            + b"*rC"
        )

        # ----------------------------------------------------
        # EJECT
        # ----------------------------------------------------

        pcl += b"\x0c"

        # ----------------------------------------------------
        # FINALIZAR JOB
        # ----------------------------------------------------

        pcl += (
            esc
            + b"E"
        )

        return bytes(
            pcl
        )

    # ========================================================
    # PREVIEW PNG
    # ========================================================

    def _gerar_preview(
        self,
        page_imagem,
    ) -> bytes:

        """
        Gera uma imagem PNG para apresentação na interface.
        Não é utilizada para impressão.
        """

        # Aproximadamente 150 DPI
        escala = (
            150
            / 72.0
        )

        pixmap = page_imagem.get_pixmap(
            matrix=fitz.Matrix(
                escala,
                escala,
            ),
            colorspace=fitz.csRGB,
            alpha=False,
        )

        return pixmap.tobytes(
            "png"
        )

    # ========================================================
    # PREPARAR
    # ========================================================

    def preparar(self):

        self.ip = self._obter_ip()

        page_imagem = self._abrir_imagem()

        try:

            self.pdf_path = (
                self._gerar_pdf(
                    page_imagem
                )
            )

            self.pcl_data = (
                self._gerar_pcl(
                    page_imagem
                )
            )

            self.preview_png = (
                self._gerar_preview(
                    page_imagem
                )
            )

            return {
                "ip": self.ip,
                "pdf_path": str(
                    self.pdf_path
                ),
                "pcl_data": self.pcl_data,
                "preview_png": self.preview_png,
                "imagem": str(
                    IMAGE_PATH
                ),
            }

        except DemonstrationError:
            raise

        except Exception as erro:

            raise DemonstrationError(
                "Não foi possível preparar "
                "o relatório de demonstração.\n\n"
                f"{erro}"
            ) from erro

    # ========================================================
    # IMPRIMIR
    # ========================================================

    def imprimir(
        self,
        timeout=15,
    ):

        if not self.pcl_data:

            raise DemonstrationError(
                "O relatório de demonstração "
                "ainda não foi preparado."
            )

        if not self.ip:

            raise DemonstrationError(
                "O endereço IP da UST "
                "não está disponível."
            )

        try:

            with socket.create_connection(
                (
                    self.ip,
                    PORTA_RAW,
                ),
                timeout=timeout,
            ) as conexao:

                conexao.sendall(
                    self.pcl_data
                )

        except OSError as erro:

            raise DemonstrationError(
                "Não foi possível enviar "
                "o relatório de demonstração "
                "para a UST.\n\n"
                f"Destino: {self.ip}:{PORTA_RAW}\n\n"
                f"{erro}"
            ) from erro

        return {
            "destino": (
                f"{self.ip}:{PORTA_RAW}"
            ),
            "pdf": (
                str(self.pdf_path)
                if self.pdf_path
                else None
            ),
        }

    # ========================================================
    # FECHAR
    # ========================================================

    def fechar(self):

        if self._imagem_doc is not None:

            try:
                self._imagem_doc.close()
            except Exception:
                pass

            self._imagem_doc = None