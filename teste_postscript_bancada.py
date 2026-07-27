import socket


IP = "192.168.14.134"
PORTA = 9100


ps = r"""%!PS

/Courier-Bold findfont
24 scalefont
setfont

100 750 moveto
(PRINTER ASSISTANT) show

/Courier findfont
14 scalefont
setfont


100 700 moveto
("TESTE DE COMUNICACAO OK") show


100 650 moveto
("LEXMARK MX611dhe") show


100 600 moveto
("PROTOCOLO: POSTSCRIPT RAW 9100") show


100 550 moveto
("STATUS: ONLINE") show


showpage
"""


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


print("Página enviada")