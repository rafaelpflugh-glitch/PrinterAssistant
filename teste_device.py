from core.device import carregar_dispositivos

lista = carregar_dispositivos()

print()

print("="*70)

print("DISPOSITIVOS IDENTIFICADOS")

print("="*70)

for d in lista:

    print()

    for k,v in d.resumo().items():

        print(f"{k:15}: {v}")