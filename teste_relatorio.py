import socket

IP = "192.168.14.151"
PORTA = 9100

pjl = b"\x1b%-12345X"
pjl += b"@PJL JOB NAME=\"TESTE_PA\"\r\n"
pjl += b"@PJL ENTER LANGUAGE=PCL\r\n"

# PCL
pjl += b"\x1bE"

# Seleciona fonte Courier 12
pjl += b"\x1b(s0p12h0s0b4099T"

# Texto
pjl += b"PRINTER ASSISTANT\r\n"
pjl += b"\r\n"
pjl += b"RELATORIO DE ATIVO\r\n"
pjl += b"\r\n"
pjl += b"FABRICANTE: Lexmark\r\n"
pjl += b"MODELO:     MX611dhe\r\n"
pjl += b"SERIAL:     701644HH03ND3\r\n"

# Finaliza a pagina
pjl += b"\x0c"

# Volta para PJL
pjl += b"\x1b%-12345X"

with socket.create_connection((IP, PORTA), timeout=10) as sock:
    sock.sendall(pjl)

print("Pagina enviada para", IP)
