import socket


IP = "192.168.14.134"
PORTA = 9100


comandos = [
    "@PJL INFO ID",
    "@PJL INFO STATUS",
    "@PJL INFO CONFIG",
    "@PJL INFO PAGECOUNT",
    "@PJL INFO MEMORY",
    "@PJL INFO VARIABLES",
    "@PJL INFO SUPPLIES",
]


for cmd in comandos:

    print("="*60)
    print(cmd)
    print("="*60)


    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    s.connect(
        (IP, PORTA)
    )


    dados = (
        "\033%-12345X" +
        cmd +
        "\r\n" +
        "\033%-12345X"
    )


    s.sendall(
        dados.encode()
    )


    resposta = s.recv(8192)

    print(
        resposta.decode(
            errors="ignore"
        )
    )


    s.close()