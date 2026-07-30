from core.lexmark import Lexmark

ip=input("IP: ")

action=input("ACTION: ")

dados={}

print()

print("Digite")

print()

print("variavel=valor")

print()

print("ENTER vazio termina")

while True:

    s=input("> ")

    if s=="":

        break

    nome,valor=s.split("=")

    dados[nome]=valor

printer=Lexmark(ip)

printer.post(action,dados)