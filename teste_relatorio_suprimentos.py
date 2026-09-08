import socket

IP = "192.168.14.134"
PORTA = 9100

pcl = b"\x1b%-12345X"
pcl += b"@PJL JOB NAME=\"PA_TESTE_RELATORIO\"\r\n"
pcl += b"@PJL ENTER LANGUAGE=PCL\r\n"

pcl += b"\x1bE"

# Courier 12 pt
pcl += b"\x1b(s0p12h0s0b4099T"

pcl += b"PRINTER ASSISTANT\r\n"
pcl += b"RELATORIO DE CONFIGURACAO E SUPRIMENTOS\r\n"
pcl += b"\r\n"

pcl += b"============================================\r\n"
pcl += b"IMPRESSORA\r\n"
pcl += b"============================================\r\n"
pcl += b"Fabricante: Lexmark\r\n"
pcl += b"Modelo:     MX611dhe\r\n"
pcl += b"Serial:     701644HH03ND3\r\n"
pcl += b"Contador:   138132\r\n"
pcl += b"Firmware:   LW70.SB7.P022-800\r\n"
pcl += b"\r\n"

pcl += b"============================================\r\n"
pcl += b"CARTUCHO\r\n"
pcl += b"============================================\r\n"
pcl += b"Fabricante: N/D\r\n"
pcl += b"Nivel:      88.0 %\r\n"
pcl += b"Capacidade: 20000\r\n"
pcl += b"Serial:     N/D\r\n"
pcl += b"\r\n"

pcl += b"============================================\r\n"
pcl += b"UNIDADE DE IMAGEM\r\n"
pcl += b"============================================\r\n"
pcl += b"Fabricante: N/D\r\n"
pcl += b"Nivel:      55.0 %\r\n"
pcl += b"Capacidade: 60000\r\n"
pcl += b"Serial:     N/D\r\n"
pcl += b"\r\n"

pcl += b"============================================\r\n"
pcl += b"KIT DE MANUTENCAO / FUSOR\r\n"
pcl += b"============================================\r\n"
pcl += b"Nivel:      31.0 %\r\n"
pcl += b"Capacidade: 200000\r\n"
pcl += b"Serial:     0000000\r\n"

pcl += b"\r\n"
pcl += b"============================================\r\n"

# Uma pagina
pcl += b"\x0c"

with socket.create_connection((IP, PORTA), timeout=10) as sock:
    sock.sendall(pcl)

print("Teste enviado para", IP)
