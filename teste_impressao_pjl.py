import socket


IP = "192.168.14.134"


def enviar(comando):

    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    s.settimeout(5)

    s.connect(
        (IP,9100)
    )

    s.send(
        comando.encode()
    )

    s.close()



pjl = (
    "\033%-12345X"
    "@PJL ENTER LANGUAGE=PCL\r\n"
)


enviar(pjl)


print("Comando enviado")