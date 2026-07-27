from tools.parser.secoes import dividir_secoes


with open(

    "sysddebug.txt",

    encoding="utf-8",

    errors="ignore"

) as arquivo:

    texto = arquivo.read()


secoes = dividir_secoes(texto)


print()

print("Quantidade de seções:")

print(len(secoes))

print()

print("=" * 50)

print()


for nome in sorted(secoes.keys())[:30]:

    print(nome)