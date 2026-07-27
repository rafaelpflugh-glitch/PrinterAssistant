from tools.parser import extrair_suprimentos, formatar


with open(
    "debug_dump.txt",
    encoding="utf-8",
    errors="ignore"
) as f:

    dados=f.read()



resultado = extrair_suprimentos(dados)


print(resultado)


print()


print(formatar(resultado))