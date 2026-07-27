from core.contexto import obter_contexto

from tools.printer import coletar_debug

from tools.parser.identificacao import extrair_identificacao
from tools.parser.modelo import identificar_modelo
from tools.parser.suprimentos import (
    extrair_suprimentos
)



def bancada():


    contexto = obter_contexto()



    if not contexto.get("ip"):

        return """

=========================================================

          PRINTER ASSISTANT - BANCADA

Nenhuma impressora selecionada.

Use:

procurar

=========================================================

"""



    ip = contexto.get("ip")



    modelo = contexto.get(
        "modelo"
    )


    confianca = contexto.get(
        "confianca",
        0
    )


    serial = contexto.get(
        "serial"
    )


    firmware = contexto.get(
        "firmware"
    )



    suprimentos = contexto.get(
        "suprimentos",
        {}
    )



    # =====================================================
    # COLETA AUTOMÁTICA SYSDEBUG
    # =====================================================


    try:


        dump = coletar_debug(ip)



        if dump and not dump.startswith("Erro"):



            identificacao = extrair_identificacao(
                dump
            )



            resultado_modelo = identificar_modelo(
                identificacao
            )



            if resultado_modelo:


                modelo = resultado_modelo.get(
                    "modelo",
                    modelo
                )


                confianca = resultado_modelo.get(
                    "confianca",
                    confianca
                )



            if not serial:


                serial = identificacao.get(
                    "serial"
                )



            if not firmware:


                firmware = identificacao.get(
                    "firmware"
                )



            # SUPRIMENTOS

            novos_suprimentos = extrair_suprimentos(
                dump
            )



            if novos_suprimentos:


                suprimentos = novos_suprimentos





    except Exception as erro:


        print(
            "Erro coleta bancada:",
            erro
        )





    if not modelo:

        modelo = "Não identificado"



    if not serial:

        serial = "-"



    if not firmware:

        firmware = "-"




    toner = suprimentos.get(
        "toner",
        {}
    )


    imagem = suprimentos.get(
        "imagem",
        {}
    )





    return f"""

=========================================================
          PRINTER ASSISTANT - BANCADA V0.4
=========================================================


IDENTIFICAÇÃO


Modelo..............{modelo}

Confiança...........{confianca}%


Serial..............{serial}

Firmware............{firmware}


IP..................{ip}



=========================================================
SUPRIMENTOS
=========================================================



TONER


Serial..............{toner.get("serial","-")}

Chip................{toner.get("chip","-")}

Nível...............{toner.get("nivel","-")}%


Páginas.............{toner.get("paginas","-")}

Restante............{toner.get("restante","-")}

Capacidade..........{toner.get("capacidade","-")}




---------------------------------------------------------



UNIDADE DE IMAGEM



Serial..............{imagem.get("serial","-")}

Nível...............{imagem.get("nivel","-")}%


Páginas.............{imagem.get("paginas","-")}





=========================================================
USB HOST FRONTAL
=========================================================


Status..............Não testado



Procedimento:


1 - Inserir pendrive FAT32


2 - Verificar detecção no painel


3 - Confirmar leitura





=========================================================
AÇÕES DISPONÍVEIS
=========================================================



IMPRESSÕES


- Página de configuração

- Página demonstração

- Relatório de ativos

- Página de menus





CONFIGURAÇÕES


- Tipo de papel

- Peso do papel

- Textura do papel





RESET


- Restaurar fábrica

- Reset rede

- Reset aplicativos





HARDWARE


- Testar USB

- Scanner ON/OFF





PROCEDIMENTOS


- Troca toner

- Troca IU

- Limpeza

- Diagnóstico





=========================================================

"""