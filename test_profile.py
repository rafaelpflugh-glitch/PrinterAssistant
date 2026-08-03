from core.session import criar_sessao

from profiles.loader import carregar_profile


sessao = criar_sessao()

sessao.carregar()


profile = carregar_profile(

    sessao.modelo()

)


print()

print("="*60)

print("PROFILE")

print("="*60)

print()

print(

    profile.info()

)