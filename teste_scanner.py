from tools.scanner import descobrir_impressoras


rede = "192.168.14.134"

impressoras = descobrir_impressoras(
    rede
)


print()

print("==============================")
print("RESULTADO")
print("==============================")


for p in impressoras:

    print()

    print("IP:", p.ip)
    print("Modelo:", p.modelo)
    print("Fabricante:", p.fabricante)
    print("Serial:", p.serial)