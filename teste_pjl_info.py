import socket


IP = "192.168.14.134"
PORTA = 9100


def pjl(comando):

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


    print(resposta.decode(errors="ignore"))



comandos = [

    "@PJL INFO ID\r\n",

    "@PJL INFO CONFIG\r\n",

    "@PJL INFO PAGECOUNT\r\n",

    "@PJL INFO MEMORY\r\n",

]


for cmd in comandos:

    print("="*50)
    print(cmd.strip())
    print("="*50)

    pjl(
        "\033%-12345X"
        + cmd
        + "\033%-12345X"
    )