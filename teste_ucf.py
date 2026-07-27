from tools.ucf_parser import UCFParser



arquivo = (
    "data/exports/"
    "export_192_168_14_134.ucf"
)



with open(

    arquivo,

    encoding="utf-8"

) as f:


    texto = f.read()



parser = UCFParser()


resultado = parser.analisar(texto)



print()

print("==============================")
print("CONFIGURAÇÃO")
print("==============================")


contador = 0


for chave, valor in resultado.items():


    print(

        chave,

        "=",

        valor

    )


    contador += 1



    if contador >= 30:

        break