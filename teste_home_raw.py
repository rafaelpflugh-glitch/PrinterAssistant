import requests


ip = "192.168.14.134"

url = f"http://{ip}/"



r = requests.get(
    url,
    timeout=10
)



print("==============================")
print("STATUS")
print("==============================")

print(r.status_code)


print()

print("==============================")
print("CONTEUDO")
print("==============================")

print(r.text[:3000])



with open(
    "data/home.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(r.text)


print()

print("Salvo data/home.html")