from core.hermes import Hermes

h = Hermes()

prompt = """

Ferramentas:

asset_report

reset_network

firmware_backup

history

Objetivo:

Quero gerar a etiqueta de ativo.

"""

print(
    h.ask(prompt)
)