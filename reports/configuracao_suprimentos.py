"""
============================================================
PRINTER ASSISTANT
RELATÓRIO DE CONFIGURAÇÃO E SUPRIMENTOS (reports/configuracao_suprimentos.py)
============================================================

Módulo de acesso direto às funções de preparação (preview),
impressão RAW 9100 (PCL) e digitalização em PDF (página única A4
em W:\\TEC\\Digitalizacao) do Relatório de Configuração e Suprimentos,
sem realizar nova coleta na impressora.
"""

from core.relatorio_suprimentos import (
    PORTA_RAW,
    PASTA_RELATORIOS,
    SuprimentosReportError,
    ReportConfiguracaoSuprimentos,
    ConfigReport,
    extrair_dados,
    montar_texto,
    preparar_relatorio_configuracao,
    gerar_pcl,
    imprimir,
    imprimir_relatorio_configuracao,
    gerar_pdf,
    digitalizar_relatorio_configuracao,
)

__all__ = [
    "PORTA_RAW",
    "PASTA_RELATORIOS",
    "SuprimentosReportError",
    "ReportConfiguracaoSuprimentos",
    "ConfigReport",
    "extrair_dados",
    "montar_texto",
    "preparar_relatorio_configuracao",
    "gerar_pcl",
    "imprimir",
    "imprimir_relatorio_configuracao",
    "gerar_pdf",
    "digitalizar_relatorio_configuracao",
]
