import socket
import time

IP = "192.168.14.134"   # coloque o IP da MX611 aqui
PORTA = 9100


pjl = b"\x1b%-12345X"
pjl += b"@PJL INFO SUPPLIES\r\n"
pjl += b"@PJL EOJ\r\n"
pjl += b"\x1b%-12345X"


print("Conectando...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)

s.connect((IP, PORTA))

print("Enviando PJL...")

s.sendall(pjl)

time.sleep(2)

try:
    resposta = s.recv(4096)
    print("Resposta:")
    print(resposta.decode(errors="ignore"))
except:
    print("Sem resposta")

s.close()

print("Finalizado")