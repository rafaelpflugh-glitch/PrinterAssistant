"""
Printer Assistant

Relatório de Configuração
"""

class ConfigReport:

    title = "config"

    description = "Relatório de configuração da impressora"

    def build(self, session, config):

        linhas = []

        linhas.append("=" * 60)
        linhas.append("CONFIGURAÇÃO DA IMPRESSORA")
        linhas.append("=" * 60)
        linhas.append("")

        linhas.append(f"Modelo.............: {session.model}")
        linhas.append(f"IP.................: {session.ip}")
        linhas.append(f"Páginas............: {session.pagecount}")
        linhas.append("")

        linhas.append("=" * 60)
        linhas.append("CONFIGURAÇÃO PJL")
        linhas.append("=" * 60)

        for chave, valor in sorted(config.items()):

            linhas.append(

                f"{chave:<30} {valor}"

            )

        linhas.append("")

        return "\n".join(linhas)