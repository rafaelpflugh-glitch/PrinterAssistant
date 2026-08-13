from core.session import Session

sessao = Session()

sessao.connect("192.168.0.50")

sessao.update_from_parser({

    "model": "Lexmark MX611de",

    "serial": "123ABC",

    "firmware": "LW71.P635",

    "memory": 524288,

    "pagecount": 137974,

    "vendor": "Lexmark"

})

print()

print("=" * 60)

print("SESSION")

print("=" * 60)

print(sessao.info())

print()

print("Duplex:")

print(sessao.has("duplex"))

print()

print("Network:")

print(sessao.has("network"))