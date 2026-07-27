from core.comandos_db import carregar


comandos = [

    "pagina_configuracao",
    "pagina_demo",
    "reset_factory",
    "scanner_on"

]


for c in comandos:

    print("====================")
    print(c)

    resultado = carregar(c)

    print(resultado)