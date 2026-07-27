# ==================================================
# ANALISADOR TÉCNICO LEXMARK
# ==================================================


def analisar_resultados(dados):


    resultado = []



    texto = str(dados).lower()



    # ==========================================
    # REDE
    # ==========================================

    if "falha" in texto and "rede" in texto:


        resultado.append(
            "Comunicação de rede apresenta falha."
        )


        resultado.append(
            "Verificar cabo de rede, IP, switch ou placa de rede."
        )



    elif "porta aberta" in texto:


        resultado.append(
            "Comunicação TCP aparentemente funcional."
        )



    # ==========================================
    # SYSDEBUG
    # ==========================================

    if "sysdebug" in texto:


        if "erro" in texto:


            resultado.append(
                "Coleta SysDebugData apresentou falha."
            )


            resultado.append(
                "Possível problema de comunicação EWS ou firmware."
            )


        else:


            resultado.append(
                "Dados internos da impressora coletados."
            )



    # ==========================================
    # EWS
    # ==========================================

    if "ews" in texto:


        if "[ok]" in texto:


            resultado.append(
                "Servidor EWS acessível."
            )


        else:


            resultado.append(
                "Não foi possível confirmar acesso ao EWS."
            )



    # ==========================================
    # USB
    # ==========================================

    if "usb" in texto:


        if "ok" in texto:


            resultado.append(
                "Interface USB respondeu corretamente."
            )


        else:


            resultado.append(
                "USB não confirmado."
            )


            resultado.append(
                "Verificar cabo, porta USB ou controlador."
            )



    # ==========================================
    # NENHUM PADRÃO
    # ==========================================

    if not resultado:


        resultado.append(
            "Nenhuma condição técnica conclusiva encontrada."
        )


        resultado.append(
            "Necessária coleta adicional de dados."
        )



    return "\n".join(resultado)