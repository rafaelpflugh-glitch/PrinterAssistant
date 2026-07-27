from core.form_scanner import FormScanner


ip = "192.168.14.134"


paginas = [

    "/cgi-bin/dynamic/printer/config/gen/general.html",

    "/cgi-bin/dynamic/printer/config/net/ip.html",

    "/cgi-bin/dynamic/printer/config/shortcuts/destinations.html",

    "/cgi-bin/dynamic/printer/config/secure/auth/manageusers.html",

    "/cgi-bin/dynamic/printer/config/gen/importexport.html"

]


scanner = FormScanner(ip)


resultado = scanner.escanear(
    paginas
)


scanner.salvar(
    resultado
)


print()

print("FINALIZADO")

print(
    len(resultado),
    "páginas com formulários"
)