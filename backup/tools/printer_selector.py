from tools.scanner import escanear_rede
from tools.printer import coletar_debug

from core.contexto import atualizar



def procurar():


    encontrados = []



    dispositivos = escanear_rede()



    print(
        "\nAnalisando dispositivos encontrados...\n"
    )



    for ip in dispositivos:


        try:


            dados = coletar_debug(ip)



            if dados and "Lexmark" in dados:


                encontrados.append(
                    {
                        "ip": ip,
                        "dados": dados
                    }
                )



        except Exception:


            pass





    if not encontrados:


        return (
            "Nenhuma Lexmark encontrada."
        )





    print(
        "\nLexmarks encontradas:\n"
    )



    for i, impressora in enumerate(encontrados):


        print(
            f"{i+1} - {impressora['ip']}"
        )





    escolha = input(
        "\nSelecionar impressora: "
    )



    try:


        selecionada = encontrados[
            int(escolha)-1
        ]



        ip = selecionada["ip"]



        dados_contexto = {


            "ip":
            ip,


            "status":
            "selecionada"

        }



        atualizar(
            dados_contexto
        )



        return (
f"""
=================================

IMPRESSORA SELECIONADA

IP:
{ip}

Hermes atualizado.

=================================
"""
        )



    except Exception:


        return (
            "Seleção inválida."
        )