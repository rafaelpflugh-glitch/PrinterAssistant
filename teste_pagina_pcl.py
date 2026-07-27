import socket


IP = "192.168.14.134"

PORTA = 9100



def enviar_pcl():

    comando = (
        "\033%-12345X"
        "@PJL ENTER LANGUAGE=PCL\r\n"
    )


    pagina = (
        "\033E"              # reset PCL

        "\033&l0O"           # orientação retrato

        "\033&l1A"           # tamanho A4

        "\033&a100H"         # posição X

        "\033&a200V"         # posição Y

        "PRINTER ASSISTANT TESTE PCL"

        "\033E"

        "\014"               # eject página
    )


    dados = (
        comando +
        pagina +
        "\033%-12345X"
    )


    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )


    s.settimeout(5)


    s.connect(
        (IP, PORTA)
    )


    s.send(
        dados.encode(
            "latin1"
        )
    )


    s.close()


    print(
        "Página enviada"
    )



enviar_pcl()