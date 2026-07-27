import socket


IP = "192.168.14.134"

PORTA = 9100


pdf = b"""%PDF-1.4
1 0 obj
<<>>
endobj
trailer
<<>>
%%EOF
"""


print("="*50)
print("PDF DIRECT CONTROL TEST")
print("="*50)


print("Enviando PDF...")


s = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

s.connect(
    (IP, PORTA)
)


s.sendall(pdf)


s.close()


print("Enviado")