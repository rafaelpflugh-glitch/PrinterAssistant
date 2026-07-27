from tools.endpoint_scanner import explorar

from tools.bancada import bancada
from core.agente import executar

from tools.analisar import analisar

from tools.painel import painel

from tools.ews import explorar
from tools.ews_parser import analisar_ews

from tools.network import testar
from tools.printer import coletar_debug
from tools.parser import extrair_suprimentos, formatar
from tools.diagnostico import diagnosticar

from tools.lexmark_reset import (
    reset_impressora,
    reset_rede,
    reset_apps
)

from tools.printer_selector import procurar
from core.session import obter

from tools.scanner import escanear_rede
from tools.usb import diagnostico_usb
from tools.painel import painel
from tools.analisar import analisar
from tools.lexmark_actions import (
    pagina_configuracao,
    pagina_demonstracao,
    relatorio_ativo,
    papel_pesado,
    textura_aspera
)

from core.contexto import atualizar



print("""
=================================

     PRINTER ASSISTANT v1.2

 Assistente Técnico Lexmark

 Hermes + Ollama Local

=================================
""")



while True:


    comando = input("\nVocê: ").strip()


    if not comando:
        continue


    if comando.lower() == "sair":

        break



    partes = comando.split()

    acao = partes[0].lower()



    # ==================================================
    # PROCURAR IMPRESSORAS
    # ==================================================

    if acao == "procurar":


        print(
            "\nProcurando impressoras Lexmark...\n"
        )


        print(
            procurar()
        )


        # ==================================================
    # PAINEL
    # ==================================================

    elif acao == "painel":


        print(
            painel()
        )

    # ==================================================
    # STATUS
    # ==================================================

    elif acao == "status":


        atual = obter()


        if atual:


            print(f"""

========== IMPRESSORA ATUAL ==========

IP:
{atual}

======================================

""")


        else:


            print(
                "\nNenhuma impressora selecionada."
            )



    # ==================================================
    # TESTE REDE
    # ==================================================

    elif acao == "teste" and len(partes) >= 3 and partes[1] == "rede":


        ip = partes[2]


        print(
            "\nTestando rede...\n"
        )


        print(
            testar(ip)
        )



    # ==================================================
    # SCAN
    # ==================================================

    elif acao == "scan":


        print(
            "\nEscaneando rede...\n"
        )


        dispositivos = escanear_rede()


        if not dispositivos:


            print(
                "Nenhum dispositivo encontrado."
            )


        else:


            for item in dispositivos:

                print("-", item)

    
    # ==================================================
    # SCAN EWS
    # ==================================================

    elif acao == "scanews":

        from tools.endpoint_scanner import explorar

        ip = partes[1] if len(partes) >= 2 else obter()

        if not ip:

            print(
                "Nenhuma impressora selecionada."
            )

            continue

        print()

        print(
            explorar(ip)
        )    


    # ==================================================
    # USB
    # ==================================================

    elif acao == "usb":


        print(
            "\nExecutando teste USB...\n"
        )


        print(
            diagnostico_usb()
        )



    # ==================================================
    # DIAGNOSTICO
    # ==================================================

    elif acao == "diagnostico":


        ip = partes[1] if len(partes) >= 2 else obter()


        if not ip:

            print(
                "Nenhuma impressora selecionada."
            )

            continue



        print(
            "\nExecutando diagnóstico completo...\n"
        )


        resultado = diagnosticar(ip)


        print(resultado)


        atualizar({

            "ip": ip,

            "ultimo_diagnostico": resultado

        })



    # ==================================================
    # DEBUG SUPRIMENTOS
    # ==================================================

    elif acao == "debug":


        ip = partes[1] if len(partes) >= 2 else obter()


        if not ip:

            print(
                "Nenhuma impressora selecionada."
            )

            continue



        print(
            "\nColetando SysDebugData...\n"
        )


        dados = coletar_debug(ip)



        if dados.startswith("Erro"):


            print(dados)



        else:


            suprimentos = extrair_suprimentos(dados)


            print(
                formatar(suprimentos)
            )


            atualizar({

                "ip": ip,

                "suprimentos": suprimentos

            })



    # ==================================================
    # EWS EXPLORER
    # ==================================================

    elif acao == "ews":


        ip = partes[1] if len(partes) >= 2 else obter()


        if not ip:

            print(
                "Nenhuma impressora selecionada."
            )

            continue



        print(
            "\nExplorando EWS Lexmark...\n"
        )


        try:


            resultado = explorar(ip)


            print(
                analisar_ews(resultado)
            )



        except Exception as erro:


            print(
                f"Erro EWS: {erro}"
            )



    # ==================================================
    # RESET
    # ==================================================

    elif acao == "reset":


        tipo = None

        ip = None



        if len(partes) >= 3:


            tipo = partes[1].lower()

            ip = partes[2]



        elif len(partes) >= 2:


            tipo = partes[1].lower()

            ip = obter()



        if not tipo or not ip:


            print("""
Uso:

reset impressora IP
reset rede IP
reset apps IP
""")


            continue



        print(
            "\nExecutando reset Lexmark...\n"
        )



        if tipo == "impressora":


            resultado = reset_impressora(ip)



        elif tipo == "rede":


            resultado = reset_rede(ip)



        elif tipo == "apps":


            resultado = reset_apps(ip)



        else:


            print(
                "Reset desconhecido."
            )

            continue



        if resultado:


            print("""
=================================

RESET ENVIADO

Aguarde a inicialização.

=================================
""")


        else:


            print(
                "Falha no reset."
            )



    # ==================================================
    # GARANTIA
    # ==================================================

    elif acao == "garantia":


        print("""
=================================

MÓDULO GARANTIA

Em desenvolvimento.

Dados futuros:

- Modelo
- Serial
- Contadores
- Peças
- Sintomas
- Histórico

=================================
""")


    # ==================================================
    # ANALISAR
    # ==================================================

    elif acao == "analisar":


        print(
            analisar()
        )


    # ==================================================
    # BANCADA
    # ==================================================

    elif acao == "bancada":


        print(
            bancada()
        )

    # ==================================================
    # HERMES
    # ==================================================

    else:


        print(
            "\nConsultando Hermes...\n"
        )


        resposta = executar(comando)


        print(
            "\nPrinter Assistant:"
        )


        print(resposta)