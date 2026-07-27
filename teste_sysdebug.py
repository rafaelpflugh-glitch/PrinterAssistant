from tools.printer import coletar_debug


ip = "192.168.14.134"


dados = coletar_debug(ip)


print(dados[:5000])