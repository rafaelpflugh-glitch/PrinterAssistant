from tools.debug import coletar_debug

texto = coletar_debug("192.168.14.134")

palavras = [

    "mx",
    "model",
    "machine",
    "product",
    "bios",
    "type",
    "name"

]

print()

print("=" * 60)

for linha in texto.splitlines():

    l = linha.lower()

    for palavra in palavras:

        if palavra in l:

            print(linha)

            break