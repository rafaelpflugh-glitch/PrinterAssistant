from core.command_executor import CommandExecutor



ip = "192.168.14.134"



hermes = CommandExecutor(ip)



resultado = hermes.executar(

    "lexmark",

    "exportar_configuracao"

)



print()

print(resultado)