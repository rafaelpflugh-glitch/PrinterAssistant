from core.form_scanner import FormScanner
import json


ip = "192.168.14.134"


paginas = [

    "/cgi-bin/dynamic/printer/config/gen/general.html",

    "/cgi-bin/dynamic/printer/config/secure/auth/manageusers.html",

    "/cgi-bin/dynamic/printer/config/gen/importexport.html"

]


scanner = FormScanner(ip)


resultado = scanner.escanear(
    paginas
)


print()

print("=" * 60)
print("DETALHES")
print("=" * 60)


print(
    json.dumps(
        resultado,
        indent=4,
        ensure_ascii=False
    )
)


scanner.salvar(resultado)