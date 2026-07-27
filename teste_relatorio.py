from tools.ucf_parser import UCFParser
from tools.config_interpreter import ConfigInterpreter



arquivo = (

"data/printers/192.168.14.134/config.ucf"

)



with open(

    arquivo,

    encoding="utf-8"

) as f:


    texto = f.read()



parser = UCFParser()


dados = parser.analisar(texto)



interpretador = ConfigInterpreter(dados)


resultado = interpretador.interpretar()



print()

print("==============================")

print("RELATORIO")

print("==============================")



for item, valor in resultado.items():

    print(

        item,

        ":",

        valor

    )