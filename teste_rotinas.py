from tools.routines import Rotinas


ip = "192.168.14.134"

r = Rotinas(ip)


print()

print("1 - Página de teste")

print("2 - Configuração")

print("3 - Estatísticas")

print()


op = input("Escolha: ")


if op == "1":

    r.pagina_teste()


elif op == "2":

    r.configuracao()


elif op == "3":

    r.estatisticas()