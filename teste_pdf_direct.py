import socket


IP = "192.168.14.134"

PORTA = 9100


arquivo = "teste.pdf"


print("="*50)
print("PDF DIRECT TEST")
print("="*50)


with open(arquivo, "rb") as f:
    pdf = f.read()


print("PDF tamanho:", len(pdf))


sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)


sock.connect(
    (IP, PORTA)
)


sock.sendall(pdf)


sock.close()


print("PDF enviado")