import socket

IP = "192.168.14.134"
PORTA = 9100

def enviar(cmd):

    dados = (
        "\033%-12345X"
        + cmd +
        "\r\n"
        + "\033%-12345X"
    )

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((IP, PORTA))
    s.send(dados.encode())
    resposta = b""

    while True:
        try:
            d = s.recv(4096)
            if not d:
                break
            resposta += d
        except:
            break

    s.close()

    print(resposta.decode(errors="ignore"))


print("="*50)
print("PJL VARIABLES")
print("="*50)

enviar("@PJL INFO VARIABLES")