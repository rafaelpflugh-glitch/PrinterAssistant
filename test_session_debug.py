from core.session import criar_sessao


sessao = criar_sessao()


print("="*60)
print("DEBUG SESSION")
print("="*60)


ok = sessao.carregar()


print()

print("Carregou:", ok)

print()

print("Ativa:")
print(sessao.ativa)


print()

print("IP:")
print(sessao.ip)


print()

print("Modelo:")
print(sessao.modelo())


print()

print("Dados completos:")
print(sessao.to_dict())