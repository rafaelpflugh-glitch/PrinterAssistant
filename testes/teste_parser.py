from pprint import pprint

from tools.parser.parser import parse_sysdebug


with open(

    "sysddebug.txt",

    encoding="utf-8",

    errors="ignore"

) as arquivo:

    texto = arquivo.read()


dados = parse_sysdebug(texto)

print()

print("IDENTIFICAÇÃO")

pprint(

    dados["identificacao"]

)

print()

print("FIRMWARE")

pprint(

    dados["firmware"]

)

print()

print("SUPRIMENTOS")

pprint(

    dados["suprimentos"]

)

print()

print("TOTAL DE SEÇÕES")

print(

    len(dados["secoes"])

)