
"""
============================================================
PRINTER ASSISTANT
SERVIÇO DE RELATÓRIOS
============================================================

Responsabilidades:

    - receber um PrinterDevice já coletado;
    - disparar os relatórios;
    - manter a interface livre de comunicação de rede;
    - não realizar nova coleta da impressora;
    - centralizar a integração entre a interface e os módulos
      existentes em reports/.

Relatórios:

    - Relatório de Ativo
    - Relatório de Configuração e Suprimentos
    - Página de Demonstração

DESTINO DA PÁGINA DE DEMONSTRAÇÃO:

    UST
    RAW 9100

    A página de demonstração utiliza a imagem oficial da
    Lexmark armazenada localmente em:

        C:\\PrinterAssistant\\assets\\print\\too_dark\\check_1.jpg

IMPORTANTE:

    A Página de Demonstração NÃO depende da identificação
    do modelo da impressora.

    Ela é uma página de teste de qualidade de impressão.

    Portanto:

        - não usa o serial da impressora;
        - não usa o fabricante;
        - não usa o modelo;
        - não faz nova coleta;
        - não tenta corrigir a identificação da máquina.

============================================================
"""

from __future__ import annotations

from pathlib import Path


# ============================================================
# ERRO CONTROLADO
# ============================================================

class ReportError(Exception):
    """
    Erro controlado durante geração ou impressão de relatório.
    """

    pass


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# ------------------------------------------------------------
# RAIZ DO PROJETO
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------
# PORTA RAW PADRÃO DA UST
# ------------------------------------------------------------

RAW_PORT = 9100


# ------------------------------------------------------------
# IMAGEM OFICIAL DA PÁGINA DE DEMONSTRAÇÃO
# ------------------------------------------------------------

DEMONSTRACAO_IMAGE = (
    PROJECT_ROOT
    / "assets"
    / "print"
    / "too_dark"
    / "check_1.jpg"
)


# ------------------------------------------------------------
# CAMINHOS ALTERNATIVOS
#
# Alguns ambientes podem ter recebido a imagem com uma
# nomenclatura diferente durante os testes.
#
# O primeiro caminho continua sendo o oficial.
# ------------------------------------------------------------

DEMONSTRACAO_IMAGE_ALTERNATIVOS = (
    DEMONSTRACAO_IMAGE,

    PROJECT_ROOT
    / "assets"
    / "print"
    / "_too_dark_check_1.jpg",

    PROJECT_ROOT
    / "assets"
    / "print"
    / "too_dark_check_1.jpg",

    PROJECT_ROOT
    / "assets"
    / "print"
    / "_too"
    / "_dark"
    / "check_1.jpg",

    PROJECT_ROOT
    / "assets"
    / "print"
    / "_too_dark"
    / "check_1.jpg",
)


# ============================================================
# SERVIÇO
# ============================================================

class ReportService:
    """
    Ponte entre a interface e os relatórios.

    IMPORTANTE:

        Este serviço NÃO realiza coleta de rede.

        O PrinterDevice recebido deve conter os dados
        previamente coletados.

    A comunicação com a impressora somente ocorre quando um
    método de impressão é explicitamente chamado.
    """

    # =========================================================
    # INICIALIZAÇÃO
    # =========================================================

    def __init__(
        self,
        device,
    ):

        self.device = device

    # =========================================================
    # VALIDAÇÃO
    # =========================================================

    def _validar_device(self):

        if self.device is None:

            raise ReportError(
                "Nenhuma impressora está selecionada."
            )

    # =========================================================
    # DADOS
    # =========================================================

    def _dados(self):

        self._validar_device()

        try:

            dados = self.device.to_dict()

        except Exception as erro:

            raise ReportError(
                "Não foi possível obter os dados "
                "da impressora selecionada.\n\n"
                f"{erro}"
            ) from erro

        if not isinstance(
            dados,
            dict,
        ):

            raise ReportError(
                "PrinterDevice.to_dict() "
                "não retornou um dicionário."
            )

        return dados

    # =========================================================
    # IDENTIFICAÇÃO
    # =========================================================

    def _identificacao(self):

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

        return identificacao

    # =========================================================
    # IP DA IMPRESSORA
    # =========================================================

    def _ip_device(self):

        """
        Obtém o IP já conhecido pelo PrinterDevice.

        Não realiza nenhuma consulta de rede.
        """

        ip = getattr(
            self.device,
            "ip",
            None,
        )

        if ip:

            return str(ip).strip()

        try:

            dados = self._dados()

            ip = dados.get(
                "ip"
            )

            if ip:

                return str(ip).strip()

        except ReportError:

            pass

        return None

    # =========================================================
    # RELATÓRIO DE ATIVO
    # =========================================================

    def imprimir_ativo(self):

        """
        Dispara o Relatório de Ativo.

        Não realiza nova coleta.

        A rotina funcional está em:

            reports.ativo
        """

        self._validar_device()

        try:

            from reports.ativo import (
                imprimir_relatorio_ativo,
            )

        except ImportError as erro:

            raise ReportError(
                "A rotina do Relatório de Ativo "
                "não foi encontrada.\n\n"
                "Arquivo esperado:\n"
                "reports/ativo.py\n\n"
                "Função esperada:\n"
                "imprimir_relatorio_ativo()"
            ) from erro

        # -----------------------------------------------------
        # EXECUÇÃO
        # -----------------------------------------------------

        try:

            resultado = (
                imprimir_relatorio_ativo(
                    self.device
                )
            )

        except TypeError:

            # -------------------------------------------------
            # COMPATIBILIDADE COM IMPLEMENTAÇÃO ANTIGA
            # -------------------------------------------------

            identificacao = (
                self._identificacao()
            )

            fabricante = identificacao.get(
                "fabricante",
                "Desconhecido",
            )

            modelo = identificacao.get(
                "modelo",
                "Desconhecido",
            )

            serial = identificacao.get(
                "serial",
                "Desconhecido",
            )

            contador = identificacao.get(
                "contador",
                "Desconhecido",
            )

            try:

                resultado = (
                    imprimir_relatorio_ativo(
                        fabricante,
                        modelo,
                        serial,
                        contador,
                    )
                )

            except Exception as erro:

                raise ReportError(
                    "Não foi possível imprimir "
                    "o Relatório de Ativo.\n\n"
                    f"{erro}"
                ) from erro

        except Exception as erro:

            raise ReportError(
                "Não foi possível imprimir "
                "o Relatório de Ativo.\n\n"
                f"{erro}"
            ) from erro

        # -----------------------------------------------------
        # RETORNO
        # -----------------------------------------------------

        if isinstance(
            resultado,
            dict,
        ):

            resultado.setdefault(
                "sucesso",
                True,
            )

            resultado.setdefault(
                "relatorio",
                "ativo",
            )

            return resultado

        return {
            "sucesso": True,
            "relatorio": "ativo",
            "resultado": resultado,
        }

    # =========================================================
    # CONFIGURAÇÃO E SUPRIMENTOS
    # =========================================================

    def imprimir_configuracao(self):

        """
        Dispara o Relatório Técnico de Configuração
        e Suprimentos.

        NÃO realiza nova coleta.

        A rotina funcional está em:

            reports/configuracao.py

        Função:

            imprimir_relatorio_configuracao(device)
        """

        self._validar_device()

        # -----------------------------------------------------
        # Garante que o PrinterDevice possui dados válidos.
        # -----------------------------------------------------

        dados = self._dados()

        try:

            from reports.configuracao import (
                imprimir_relatorio_configuracao,
            )

        except ImportError as erro:

            raise ReportError(
                "A rotina funcional do "
                "Relatório de Configuração "
                "e Suprimentos não foi encontrada.\n\n"
                "Arquivo esperado:\n"
                "reports/configuracao.py\n\n"
                "Função esperada:\n"
                "imprimir_relatorio_configuracao(device)"
            ) from erro

        # -----------------------------------------------------
        # IMPRESSÃO
        # -----------------------------------------------------

        try:

            resultado = (
                imprimir_relatorio_configuracao(
                    self.device
                )
            )

        except Exception as erro:

            raise ReportError(
                "Não foi possível imprimir "
                "o Relatório de Configuração "
                "e Suprimentos.\n\n"
                f"{erro}"
            ) from erro

        # -----------------------------------------------------
        # IP
        # -----------------------------------------------------

        ip = self._ip_device()

        # -----------------------------------------------------
        # RETORNO
        # -----------------------------------------------------

        if isinstance(
            resultado,
            dict,
        ):

            resultado.setdefault(
                "sucesso",
                True,
            )

            resultado.setdefault(
                "relatorio",
                "configuracao",
            )

            if ip:

                resultado.setdefault(
                    "ip",
                    ip,
                )

            resultado.setdefault(
                "porta",
                RAW_PORT,
            )

            return resultado

        return {
            "sucesso": True,
            "relatorio": "configuracao",
            "ip": ip,
            "porta": RAW_PORT,
            "resultado": resultado,
        }

    # =========================================================
    # LOCALIZAR IMAGEM DA DEMONSTRAÇÃO
    # =========================================================

    @classmethod
    def _localizar_imagem_demonstracao(
        cls,
    ):
        """
        Localiza a imagem oficial da Página de Demonstração.

        Não baixa nada da internet.

        A imagem precisa existir localmente.

        Retorna:
            pathlib.Path

        Levanta:
            ReportError
        """

        # -----------------------------------------------------
        # 1. TENTA O CAMINHO OFICIAL
        # -----------------------------------------------------

        for caminho in DEMONSTRACAO_IMAGE_ALTERNATIVOS:

            try:

                if caminho.is_file():

                    return caminho

            except OSError:

                continue

        # -----------------------------------------------------
        # 2. ERRO DETALHADO
        # -----------------------------------------------------

        caminhos = "\n".join(
            f"  - {caminho}"
            for caminho
            in DEMONSTRACAO_IMAGE_ALTERNATIVOS
        )

        raise ReportError(
            "A imagem da Página de Demonstração "
            "não foi encontrada.\n\n"
            "Caminhos procurados:\n"
            f"{caminhos}\n\n"
            "Confirme se a imagem oficial da Lexmark "
            "foi salva em:\n"
            f"{DEMONSTRACAO_IMAGE}"
        )

    # =========================================================
    # PREPARAR DEMONSTRAÇÃO
    # =========================================================

    def preparar_demonstracao(self):

        """
        Prepara a Página de Demonstração.

        IMPORTANTE:

            Esta etapa NÃO imprime.

            Também NÃO realiza comunicação com a impressora.

        A função existe para que a interface possa verificar
        previamente se todos os recursos necessários estão
        disponíveis.

        Retorna um dicionário compatível com o PrinterView.
        """

        # -----------------------------------------------------
        # Não exigimos identificação correta do modelo.
        #
        # A demonstração é uma página de qualidade e pode ser
        # usada mesmo que a identificação exibida na interface
        # esteja temporariamente incorreta.
        # -----------------------------------------------------

        imagem = (
            self._localizar_imagem_demonstracao()
        )

        tamanho = None

        try:

            tamanho = imagem.stat().st_size

        except OSError:

            pass

        # -----------------------------------------------------
        # TEXTO PARA A INTERFACE
        #
        # O PrinterView atual trabalha com "texto" no preview.
        # Aqui fornecemos uma descrição técnica sem fingir que
        # isso é uma prévia gráfica da página.
        # -----------------------------------------------------

        texto = (
            "PRINTER ASSISTANT\n"
            "PÁGINA DE DEMONSTRAÇÃO\n"
            "\n"
            "Finalidade:\n"
            "Teste visual da qualidade de impressão.\n"
            "\n"
            "Origem:\n"
            "Imagem oficial Lexmark.\n"
            "\n"
            "Arquivo:\n"
            f"{imagem}\n"
            "\n"
            "Destino:\n"
            "UST\n"
            f"RAW {RAW_PORT}\n"
            "\n"
            "A página será enviada como um único job "
            "de demonstração.\n"
            "\n"
            "Nenhuma nova coleta será realizada."
        )

        resultado = {
            "sucesso": True,
            "relatorio": "demonstracao",
            "texto": texto,
            "imagem": str(imagem),
            "arquivo": str(imagem),
            "destino": "UST",
            "porta": RAW_PORT,
        }

        if tamanho is not None:

            resultado["tamanho_arquivo"] = tamanho

        return resultado

    # =========================================================
    # IMPRIMIR DEMONSTRAÇÃO
    # =========================================================

    def imprimir_demonstracao(self):

        """
        Imprime a Página de Demonstração na UST.

        IMPORTANTE:

            A implementação física da página fica em:

                reports.demonstracao

            Este serviço apenas fornece a imagem correta e
            encaminha o PrinterDevice/IP necessário.

        NÃO realiza nova coleta da impressora.
        """

        # -----------------------------------------------------
        # A imagem precisa existir antes de qualquer tentativa
        # de impressão.
        # -----------------------------------------------------

        imagem = (
            self._localizar_imagem_demonstracao()
        )

        # -----------------------------------------------------
        # TENTA CARREGAR O MÓDULO FUNCIONAL
        # -----------------------------------------------------

        try:

            from reports.demonstracao import (
                imprimir_relatorio_demonstracao,
            )

        except ImportError as erro:

            raise ReportError(
                "A rotina da Página de Demonstração "
                "não foi encontrada.\n\n"
                "Arquivo esperado:\n"
                "reports/demonstracao.py\n\n"
                "Função esperada:\n"
                "imprimir_relatorio_demonstracao(...)\n\n"
                "A imagem foi localizada corretamente em:\n"
                f"{imagem}"
            ) from erro

        # -----------------------------------------------------
        # IP JÁ CONHECIDO
        # -----------------------------------------------------

        ip = self._ip_device()

        # -----------------------------------------------------
        # EXECUÇÃO
        #
        # A nova implementação deve preferencialmente receber:
        #
        #     imagem
        #     device
        #
        # Dessa maneira a rotina pode utilizar o IP já coletado
        # sem precisar realizar nova descoberta.
        # -----------------------------------------------------

        try:

            resultado = (
                imprimir_relatorio_demonstracao(
                    device=self.device,
                    imagem=str(imagem),
                )
            )

        except TypeError:

            # -------------------------------------------------
            # COMPATIBILIDADE
            #
            # Permite uma implementação que receba apenas
            # o caminho da imagem.
            # -------------------------------------------------

            try:

                resultado = (
                    imprimir_relatorio_demonstracao(
                        str(imagem)
                    )
                )

            except TypeError:

                # ---------------------------------------------
                # ÚLTIMO FORMATO COMPATÍVEL:
                #
                # imagem + IP
                # ---------------------------------------------

                try:

                    resultado = (
                        imprimir_relatorio_demonstracao(
                            str(imagem),
                            ip,
                        )
                    )

                except Exception as erro:

                    raise ReportError(
                        "Não foi possível imprimir "
                        "a Página de Demonstração.\n\n"
                        f"{erro}"
                    ) from erro

            except Exception as erro:

                raise ReportError(
                    "Não foi possível imprimir "
                    "a Página de Demonstração.\n\n"
                    f"{erro}"
                ) from erro

        except Exception as erro:

            raise ReportError(
                "Não foi possível imprimir "
                "a Página de Demonstração.\n\n"
                f"{erro}"
            ) from erro

        # -----------------------------------------------------
        # RETORNO NORMALIZADO
        # -----------------------------------------------------

        if isinstance(
            resultado,
            dict,
        ):

            resultado.setdefault(
                "sucesso",
                True,
            )

            resultado.setdefault(
                "relatorio",
                "demonstracao",
            )

            resultado.setdefault(
                "imagem",
                str(imagem),
            )

            resultado.setdefault(
                "destino",
                "UST",
            )

            resultado.setdefault(
                "porta",
                RAW_PORT,
            )

            if ip:

                resultado.setdefault(
                    "ip",
                    ip,
                )

            return resultado

        return {
            "sucesso": True,
            "relatorio": "demonstracao",
            "imagem": str(imagem),
            "destino": "UST",
            "ip": ip,
            "porta": RAW_PORT,
            "resultado": resultado,
        }

    # =========================================================
    # INFORMAÇÕES DA DEMONSTRAÇÃO
    # =========================================================

    def informacoes_demonstracao(self):

        """
        Retorna informações da Página de Demonstração
        sem imprimir e sem comunicar com a impressora.

        Útil para testes e diagnóstico.
        """

        imagem = (
            self._localizar_imagem_demonstracao()
        )

        try:

            tamanho = imagem.stat().st_size

        except OSError:

            tamanho = None

        return {
            "relatorio": "demonstracao",
            "imagem": str(imagem),
            "existe": imagem.is_file(),
            "destino": "UST",
            "ip": self._ip_device(),
            "porta": RAW_PORT,
            "tamanho_arquivo": tamanho,
        }

