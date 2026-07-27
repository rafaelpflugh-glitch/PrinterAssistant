from core.printer_memory import PrinterMemory


ip = "192.168.14.134"


memoria = PrinterMemory(ip)


dados = {

    "ip": ip,

    "fabricante": "Lexmark",

    "modelo": "MX611",

    "serial": "701644HH03ND3",

    "firmware": "LW70.SB7.P022"

}



arquivo = memoria.salvar_info(dados)


print()
print("==============================")
print("MEMÓRIA")
print("==============================")
print("Arquivo criado:")
print(arquivo)