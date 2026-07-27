from tools.identify import identificar



ip = "192.168.14.134"



resultado = identificar(ip)



print()

print("==============================")

print("IDENTIFICAÇÃO")

print("==============================")


for chave,valor in resultado.items():

    print(
        chave,
        ":",
        valor
    )