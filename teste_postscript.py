import socket


IP = "192.168.14.134"
PORTA = 9100


ps = r"""
%!PS
/Courier findfont
30 scalefont
setfont

100 700 moveto
(PRINTER ASSISTANT TESTE POSTSCRIPT) show

100 650 moveto
(LEXMARK MX611) show

showpage
"""


print("="*50)
print("POSTSCRIPT TEST")
print("="*50)


s = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

s.connect(
    (IP, PORTA)
)

s.sendall(
    ps.encode("ascii")
)

s.close()


print("Enviado")