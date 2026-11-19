"""
============================================================

PRINTER ASSISTANT

SERVIÇO DE RELATÓRIOS
=====================

Responsabilidades:

- receber um PrinterDevice já coletado;
- disparar os relatórios;
- preparar relatórios sem nova comunicação;
- manter a interface livre de comunicação de rede;
- não realizar nova coleta da impressora;
- centralizar a integração entre a interface e os módulos
  existentes.

Relatórios:

- Relatório de Ativo
- Relatório de Configuração e Suprimentos
- Página de Demonstração

IMPORTANTE:

Os métodos de preparação e digitalização trabalham
exclusivamente com os dados já existentes no PrinterDevice.

DIGITALIZAR NÃO realiza nova coleta.
DIGITALIZAR NÃO envia nada para a impressora.

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_PORT = 9100

DEMONSTRACAO_IMAGE = (
    PROJECT_ROOT
    / "assets"
    / "print"
    / "too_dark"
    / "check_1.jpg"
)

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
    / "_too"
    / "_dark"
    / "check_1.jpg",

    PROJECT_ROOT
    / "assets"
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

    def __init__(
        self,
        device,
    ):
        self.device = device

        # ----------------------------------------------------
        # Marcas informadas manualmente pelo usuário.
        #
        # Elas não são coletadas da impressora.
        #
        # Devem ser preenchidas antes da geração do relatório.
        # ----------------------------------------------------

        self.marca_cartucho = None
        self.marca_unidade_imagem = None

    # ========================================================
    # VALIDAÇÃO
    # ========================================================

    def _validar_device(self):
        if self.device is None:
            raise ReportError(
                "Nenhuma impressora está selecionada."
            )

    # ========================================================
    # MARCAS DOS SUPRIMENTOS
    # ========================================================

    def definir_marcas_suprimentos(
        self,
        marca_cartucho,
        marca_unidade_imagem,
    ):
        """
        Define as marcas informadas manualmente para o relatório.

        Essas informações não são obtidas da impressora.

        A partir deste momento elas serão utilizadas por:

        - VISUALIZAR
        - DIGITALIZAR
        - IMPRIMIR
        """

        marca_cartucho = (
            str(marca_cartucho).strip()
            if marca_cartucho is not None
            else ""
        )

        marca_unidade_imagem = (
            str(marca_unidade_imagem).strip()
            if marca_unidade_imagem is not None
            else ""
        )

        if not marca_cartucho:
            raise ReportError(
                "Informe a marca do cartucho de toner."
            )

        if not marca_unidade_imagem:
            raise ReportError(
                "Informe a marca da unidade de imagem."
            )

        self.marca_cartucho = marca_cartucho
        self.marca_unidade_imagem = (
            marca_unidade_imagem
        )

        return True

    # ========================================================
    # VALIDAÇÃO DAS MARCAS
    # ========================================================

    def _validar_marcas_suprimentos(self):
        """
        Garante que as duas marcas obrigatórias foram
        informadas antes da geração do relatório.
        """

        if not self.marca_cartucho:
            raise ReportError(
                "A marca do cartucho de toner ainda não foi "
                "informada."
            )

        if not self.marca_unidade_imagem:
            raise ReportError(
                "A marca da unidade de imagem ainda não foi "
                "informada."
            )

    # ========================================================
    # DADOS
    # ========================================================

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

    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

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

    # ========================================================
    # IP DA IMPRESSORA
    # ========================================================

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

    # ========================================================
    # RELATÓRIO DE ATIVO
    # ========================================================

    def preparar_ativo(
        self,
        toner_presente=None,
        unidade_presente=None,
        data_emissao=None,
    ):
        """
        Prepara a visualização do Relatório de Ativo sem imprimir.
        """
        self._validar_device()
        try:
            from reports.ativo import (
                extrair_dados,
                contador_texto,
                IMPRESSORA_TSC,
                PORTA_TSC,
            )
            (
                fabricante,
                modelo,
                serial,
                contador,
                status_toner,
                status_unidade,
            ) = extrair_dados(
                self.device,
                toner_presente=toner_presente,
                unidade_presente=unidade_presente,
            )
            cont_fmt = contador_texto(contador)
            dest_ip = IMPRESSORA_TSC
            try:
                from core.config import resolver_ip
                dest_ip = resolver_ip(IMPRESSORA_TSC, tipo="relatorio")
            except Exception:
                pass
        except Exception:
            ident = self._identificacao()
            fabricante = ident.get("fabricante", "DESCONHECIDO")
            modelo = ident.get("modelo", "DESCONHECIDO")
            serial = ident.get("serial", "SEM SERIAL")
            cont_fmt = str(ident.get("contador", "N/D"))
            status_toner = "INSTALADO" if toner_presente else "NAO ACOMPANHA"
            status_unidade = "INSTALADA" if unidade_presente else "NAO ACOMPANHA"
            dest_ip = "192.168.14.151"
            PORTA_TSC = 9100

        if data_emissao is None:
            from datetime import datetime
            data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

        if "CANON" in str(fabricante).upper() or "INTEGRADA" in str(status_unidade).upper():
            bloco_suprimentos = (
                f"SISTEMA           : CARTUCHO INTEGRADO\n"
                f"TONER             : {status_toner}\n"
            )
        else:
            bloco_suprimentos = (
                f"TONER             : {status_toner}\n"
                f"UNIDADE DE IMAGEM : {status_unidade}\n"
            )

        texto = (
            "PRINTER ASSISTANT\n"
            "RELATÓRIO DE ATIVO\n"
            "\n"
            "----------------------------------------\n"
            f"FABRICANTE        : {fabricante}\n"
            f"MODELO            : {modelo}\n"
            f"NÚMERO DE SÉRIE   : {serial}\n"
            f"CONTADOR          : {cont_fmt}\n"
            f"{bloco_suprimentos}"
            f"DATA DE EMISSÃO   : {data_emissao}\n"
            "----------------------------------------\n"
            "\n"
            "CÓDIGO DE BARRAS\n"
            f"CODE 128: {serial}\n"
            "\n"
            "DESTINO:\n"
            f"TSC {dest_ip}:{PORTA_TSC}\n"
            "100 x 150 mm • GAP 2 mm\n"
            "\n"
            "A etiqueta será enviada diretamente para a TSC.\n"
            "Nenhuma nova coleta será realizada."
        )

        return {
            "sucesso": True,
            "relatorio": "ativo",
            "texto": texto,
            "destino": f"TSC {dest_ip}:{PORTA_TSC}",
            "status_toner": status_toner,
            "status_unidade": status_unidade,
            "data_emissao": data_emissao,
            "toner_presente": "INSTALADO" in status_toner,
            "unidade_presente": "INSTALADA" in status_unidade,
        }

    def imprimir_ativo(
        self,
        toner_presente=None,
        unidade_presente=None,
        data_emissao=None,
    ):
        """
        Dispara o Relatório de Ativo.
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

        try:
            resultado = (
                imprimir_relatorio_ativo(
                    self.device,
                    toner_presente=toner_presente,
                    unidade_presente=unidade_presente,
                    data_emissao=data_emissao,
                )
            )

        except TypeError:
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

    # ========================================================
    # CONFIGURAÇÃO E SUPRIMENTOS
    # ========================================================

    def preparar_configuracao(self):
        """
        Prepara o Relatório de Configuração e Suprimentos.

        NÃO imprime.
        NÃO gera PCL.
        NÃO realiza nova coleta.
        NÃO realiza comunicação de rede.

        As marcas informadas manualmente são incorporadas
        ao mesmo texto que será utilizado para:

        - VISUALIZAR
        - DIGITALIZAR
        - IMPRIMIR
        """

        self._validar_device()
        self._validar_marcas_suprimentos()

        try:
            from core.relatorio_suprimentos import (
                preparar_relatorio_configuracao,
            )

        except ImportError as erro:
            raise ReportError(
                "A rotina de preparação do "
                "Relatório de Configuração "
                "e Suprimentos não foi encontrada.\n\n"
                "Arquivo esperado:\n"
                "core/relatorio_suprimentos.py"
            ) from erro

        try:
            resultado = (
                preparar_relatorio_configuracao(
                    self.device,
                    marca_cartucho=self.marca_cartucho,
                    marca_unidade_imagem=(
                        self.marca_unidade_imagem
                    ),
                )
            )

        except Exception as erro:
            raise ReportError(
                "Não foi possível preparar "
                "o Relatório de Configuração "
                "e Suprimentos.\n\n"
                f"{erro}"
            ) from erro

        if not isinstance(
            resultado,
            dict,
        ):
            raise ReportError(
                "A preparação do Relatório de "
                "Configuração e Suprimentos "
                "não retornou um dicionário."
            )

        resultado.setdefault(
            "sucesso",
            True,
        )

        resultado.setdefault(
            "relatorio",
            "configuracao",
        )

        resultado.setdefault(
            "tipo",
            "configuracao_e_suprimentos",
        )

        ip = self._ip_device()

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

    # ========================================================
    # DIGITALIZAR CONFIGURAÇÃO
    # ========================================================

    def digitalizar_configuracao(self):
        """
        Cria a cópia digital em PDF do Relatório de
        Configuração e Suprimentos.

        DIGITALIZAR NÃO significa coletar novamente.

        Não executa:

        - device.coletar()
        - PJL
        - SYSDEBUG
        - SNMP
        - HTTP
        - conexão com a impressora
        - impressão
        """

        self._validar_device()
        self._validar_marcas_suprimentos()

        try:
            from core.relatorio_suprimentos import (
                digitalizar_relatorio_configuracao,
            )

        except ImportError as erro:
            raise ReportError(
                "A rotina de digitalização do "
                "Relatório de Configuração "
                "e Suprimentos não foi encontrada.\n\n"
                "Arquivo esperado:\n"
                "core/relatorio_suprimentos.py"
            ) from erro

        try:
            resultado = (
                digitalizar_relatorio_configuracao(
                    self.device,
                    marca_cartucho=self.marca_cartucho,
                    marca_unidade_imagem=(
                        self.marca_unidade_imagem
                    ),
                )
            )

        except Exception as erro:
            raise ReportError(
                "Não foi possível gerar o PDF do "
                "Relatório de Configuração "
                "e Suprimentos.\n\n"
                f"{erro}"
            ) from erro

        if not isinstance(
            resultado,
            dict,
        ):
            raise ReportError(
                "A digitalização do Relatório de "
                "Configuração e Suprimentos "
                "não retornou um dicionário."
            )

        resultado.setdefault(
            "sucesso",
            True,
        )

        resultado.setdefault(
            "relatorio",
            "configuracao",
        )

        resultado.setdefault(
            "tipo",
            "configuracao_e_suprimentos",
        )

        ip = self._ip_device()

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

    # ========================================================
    # IMPRESSÃO — CONFIGURAÇÃO E SUPRIMENTOS
    # ========================================================

    def imprimir_configuracao(self):
        """
        Dispara o Relatório Técnico de Configuração
        e Suprimentos.

        NÃO realiza nova coleta.

        As marcas informadas manualmente são incorporadas
        ao relatório impresso.
        """

        self._validar_device()
        self._validar_marcas_suprimentos()

        # Garante que o PrinterDevice possui dados válidos.
        self._dados()

        try:
            from core.relatorio_suprimentos import (
                imprimir_relatorio_configuracao,
            )

        except ImportError as erro:
            raise ReportError(
                "A rotina funcional do "
                "Relatório de Configuração "
                "e Suprimentos não foi encontrada.\n\n"
                "Arquivo esperado:\n"
                "core/relatorio_suprimentos.py"
            ) from erro

        try:
            resultado = (
                imprimir_relatorio_configuracao(
                    self.device,
                    marca_cartucho=self.marca_cartucho,
                    marca_unidade_imagem=(
                        self.marca_unidade_imagem
                    ),
                )
            )

        except Exception as erro:
            raise ReportError(
                "Não foi possível imprimir "
                "o Relatório de Configuração "
                "e Suprimentos.\n\n"
                f"{erro}"
            ) from erro

        ip = self._ip_device()

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

            resultado.setdefault(
                "tipo",
                "configuracao_e_suprimentos",
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
            "tipo": "configuracao_e_suprimentos",
            "ip": ip,
            "porta": RAW_PORT,
            "resultado": resultado,
        }

    # Aliases de compatibilidade para a interface
    preparar_configuracao_suprimentos = preparar_configuracao
    digitalizar_configuracao_suprimentos = digitalizar_configuracao
    imprimir_configuracao_suprimentos = imprimir_configuracao

    # ========================================================
    # ANÁLISE DE UNIDADE DE IMAGEM
    # ========================================================

    def preparar_analise_unidade_imagem(self):
        """
        Prepara o Relatório de Análise da Unidade de Imagem sem nova coleta.
        """
        self._validar_device()
        try:
            from reports.analise_unidade_imagem import (
                preparar_analise_unidade,
            )
        except ImportError as erro:
            raise ReportError(
                "O módulo de Análise de Unidade de Imagem não foi encontrado.\n\n"
                "Arquivo esperado:\n"
                "reports/analise_unidade_imagem.py"
            ) from erro

        try:
            resultado = preparar_analise_unidade(self.device)
        except Exception as erro:
            raise ReportError(
                "Não foi possível preparar a Análise da Unidade de Imagem.\n\n"
                f"{erro}"
            ) from erro

        if isinstance(resultado, dict):
            resultado.setdefault("sucesso", True)
            resultado.setdefault("relatorio", "analise_unidade_imagem")
            return resultado

        return {
            "sucesso": True,
            "relatorio": "analise_unidade_imagem",
            "texto": str(resultado),
        }

    def imprimir_analise_unidade_imagem(self):
        """
        Imprime o Relatório de Análise da Unidade de Imagem via porta RAW 9100.
        """
        self._validar_device()
        try:
            from reports.analise_unidade_imagem import (
                imprimir_analise_unidade,
            )
        except ImportError as erro:
            raise ReportError(
                "O módulo de Análise de Unidade de Imagem não foi encontrado.\n\n"
                "Arquivo esperado:\n"
                "reports/analise_unidade_imagem.py"
            ) from erro

        try:
            resultado = imprimir_analise_unidade(self.device)
        except Exception as erro:
            raise ReportError(
                "Não foi possível imprimir a Análise da Unidade de Imagem.\n\n"
                f"{erro}"
            ) from erro

        return {
            "sucesso": True,
            "relatorio": "analise_unidade_imagem",
            "ip": self._ip_device(),
            "porta": RAW_PORT,
            "resultado": resultado,
        }

    def digitalizar_analise_unidade_imagem(self):
        """
        Digitaliza em PDF o Relatório de Análise da Unidade de Imagem.
        """
        self._validar_device()
        try:
            from reports.analise_unidade_imagem import (
                digitalizar_analise_unidade,
            )
        except ImportError as erro:
            raise ReportError(
                "O módulo de Análise de Unidade de Imagem não foi encontrado.\n\n"
                "Arquivo esperado:\n"
                "reports/analise_unidade_imagem.py"
            ) from erro

        try:
            resultado = digitalizar_analise_unidade(self.device)
        except Exception as erro:
            raise ReportError(
                "Não foi possível digitalizar a Análise da Unidade de Imagem.\n\n"
                f"{erro}"
            ) from erro

        if isinstance(resultado, dict):
            resultado.setdefault("sucesso", True)
            resultado.setdefault("relatorio", "analise_unidade_imagem")
            return resultado

        return {
            "sucesso": True,
            "relatorio": "analise_unidade_imagem",
            "arquivo": str(resultado),
        }

    preparar_analise_unidade = preparar_analise_unidade_imagem
    imprimir_analise_unidade = imprimir_analise_unidade_imagem
    digitalizar_analise_unidade = digitalizar_analise_unidade_imagem

    # ========================================================
    # LOCALIZAR IMAGEM DA DEMONSTRAÇÃO
    # ========================================================

    @classmethod
    def _localizar_imagem_demonstracao(
        cls,
    ):
        """
        Localiza a imagem oficial da Página de Demonstração.

        Não baixa nada da internet.
        """

        for caminho in DEMONSTRACAO_IMAGE_ALTERNATIVOS:
            try:
                if caminho.is_file():
                    return caminho
            except OSError:
                continue

        caminhos = "\n".join(
            f"  - {caminho}"
            for caminho in DEMONSTRACAO_IMAGE_ALTERNATIVOS
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

    # ========================================================
    # PREPARAR DEMONSTRAÇÃO
    # ========================================================

    def preparar_demonstracao(self):
        """
        Prepara a Página de Demonstração.

        NÃO imprime.
        NÃO realiza comunicação com a impressora.
        """

        imagem = (
            self._localizar_imagem_demonstracao()
        )

        tamanho = None

        try:
            tamanho = imagem.stat().st_size
        except OSError:
            pass

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

    # ========================================================
    # IMPRIMIR DEMONSTRAÇÃO
    # ========================================================

    def imprimir_demonstracao(self):
        """
        Imprime a Página de Demonstração na UST.

        NÃO realiza nova coleta.
        """

        imagem = (
            self._localizar_imagem_demonstracao()
        )

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
                f"A imagem foi localizada em:\n{imagem}"
            ) from erro

        ip = self._ip_device()

        try:
            resultado = (
                imprimir_relatorio_demonstracao(
                    device=self.device,
                    imagem=str(imagem),
                )
            )

        except TypeError:
            try:
                resultado = (
                    imprimir_relatorio_demonstracao(
                        str(imagem)
                    )
                )

            except TypeError:
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

    # ========================================================
    # INFORMAÇÕES DA DEMONSTRAÇÃO
    # ========================================================

    def informacoes_demonstracao(self):
        """
        Retorna informações da Página de Demonstração
        sem imprimir e sem comunicar com a impressora.
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


# ============================================================
# FIM DO SERVIÇO
# ============================================================