import socket
import time


# ======================================
# CONFIGURAÇÃO
# ======================================

IP = "192.168.14.134"
PORTA = 9100


# ======================================
# COMANDO PJL
# ======================================

COMANDO = b"""
\x1b%-12345X
@PJL INFO VARIABLES
@PJL EOJ
\x1b%-12345X
"""


# ======================================
# ENVIO
# ======================================

def enviar_pjl():

    print("="*50)
    print("TESTE PJL INFO VARIABLES")
    print("="*50)

    print()
    print("Enviando para:", IP)
    print()


    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    s.settimeout(10)


    try:

        s.connect(
            (IP, PORTA)
        )


        s.sendall(
            COMANDO
        )


        time.sleep(2)


        resposta = b""


        while True:

            try:

                parte = s.recv(4096)

                if not parte:
                    break

                resposta += parte


            except socket.timeout:

                break



        print(
            resposta.decode(
                "latin1",
                errors="ignore"
            )
        )


    except Exception as e:

        print(
            "ERRO:",
            e
        )


    finally:

        s.close()



# ======================================
# START
# ======================================

enviar_pjl()