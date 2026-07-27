from datetime import datetime
import os


PASTA = "relatorios"



def criar_relatorio(dados):


    if not os.path.exists(PASTA):

        os.makedirs(PASTA)



    nome = (
        datetime.now()
        .strftime(
            "relatorio_%d_%m_%Y_%H_%M_%S.txt"
        )
    )



    caminho = os.path.join(
        PASTA,
        nome
    )



    texto = f"""

=================================
RELATÓRIO TÉCNICO LEXMARK
=================================


DATA:

{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}



IMPRESSORA:

IP:
{dados.get("ip")}


MODELO:
{dados.get("modelo")}


SERIAL:
{dados.get("serial")}



=================================

AÇÃO EXECUTADA:

{dados.get("acao")}



=================================

RESULTADO:

{dados.get("resultado")}



=================================

OBSERVAÇÃO HERMES:

{dados.get("analise")}


=================================

"""


    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:


        arquivo.write(
            texto
        )



    return caminho