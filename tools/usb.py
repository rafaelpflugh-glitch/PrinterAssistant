import subprocess



def diagnostico_usb():

    resultado = []


    resultado.append(
"""
========== TESTE USB ==========
"""
    )


    try:


        comando = (
            'wmic printer get Name,PortName,Status'
        )


        resposta = subprocess.check_output(
            comando,
            shell=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )



        linhas = resposta.splitlines()


        usb_ok = False



        for linha in linhas:


            linha = linha.strip()



            if not linha:
                continue



            if "USB" in linha.upper():


                usb_ok = True



                resultado.append(
                    "USB OK"
                )


                resultado.append(
                    linha
                )



        if not usb_ok:


            resultado.append(
"""
USB NÃO DETECTADO

Verifique:

- cabo USB
- porta USB da impressora
- driver instalado
- impressora ligada
"""
            )



    except Exception as erro:


        resultado.append(
            f"Erro no teste USB: {erro}"
        )



    resultado.append(
"""
==============================
"""
    )


    return "\n".join(resultado)