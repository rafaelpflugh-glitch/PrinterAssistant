import socket


IP = "192.168.14.134"

PORTA = 9100


def enviar_pjl(comando):

    print("="*50)
    print("ENVIANDO PJL")
    print("="*50)

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        s.settimeout(5)

        s.connect(
            (IP, PORTA)
        )


        s.send(
            comando.encode()
        )


        resposta = b""


        while True:

            try:
                dados = s.recv(4096)

                if not dados:
                    break

                resposta += dados

            except:
                break


        s.close()


        print(
            resposta.decode(
                errors="ignore"
            )
        )


    except Exception as e:

        print(
            "ERRO:",
            e
        )



# consulta status
enviar_pjl(
    "\033%-12345X@PJL INFO STATUS\r\n"
    "\033%-12345X"
)