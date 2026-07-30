def analisar_ews(texto):


    linhas = texto.splitlines()


    resultado=[]


    resultado.append(
        "\n===== ANALISADOR EWS =====\n"
    )


    for linha in linhas:


        if "[OK]" in linha:

            resultado.append(
                "✔ "+linha
            )


        elif "✓" in linha:

            resultado.append(
                linha
            )



    resultado.append(
        "\n==========================="
    )


    return "\n".join(resultado)