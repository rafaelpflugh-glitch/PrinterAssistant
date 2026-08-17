
import requests

PRINTER = "192.168.14.134"

URL = (
    f"http://{PRINTER}"
    "/cgi-bin/posttest/printer/config/paper/paperweight.html"
)

# Primeiro teste:
# Papel comum = PESADO
#
# Mantemos os demais valores exatamente como estavam
# quando a página foi capturada.

payload = {
    "0.system.1824": "2",
    "0.system.1832": "1",
    "0.system.1830": "1",
    "0.system.4619": "1",
    "0.system.1834": "1",
    "0.system.1838": "1",
    "0.system.1842": "1",
    "0.system.4820": "2",
    "0.system.1836": "1",
    "0.system.1840": "1",
    "0.system.1828": "1",
    "0.system.4595": "0",
    "0.system.4602": "2",
    "0.system.1826": "2",
    "0.system.1844": "1",
    "0.system.1848": "1",
    "0.system.1852": "1",
    "0.system.1856": "1",
    "0.system.1860": "1",
    "0.system.1864": "1",
}

print()
print("=" * 60)
print("PRINTER ASSISTANT")
print("TESTE DE CONFIGURAÇÃO - PESO DO PAPEL")
print("=" * 60)
print()

print("Impressora :", PRINTER)
print("Configuração: Papel comum = PESADO")
print()

print("Enviando POST...")

try:

    response = requests.post(
        URL,
        data=payload,
        timeout=10
    )

    print()
    print("HTTP:", response.status_code)
    print()

    if response.status_code == 200:
        print("[OK] Impressora aceitou a requisição.")
    else:
        print("[ERRO] Resposta HTTP inesperada.")

    print()
    print("URL:")
    print(URL)

    print()
    print("Payload enviado:")

    for name, value in payload.items():
        print(f"  {name} = {value}")

except requests.RequestException as e:

    print()
    print("[ERRO] Falha na comunicação:")
    print(e)

print()

