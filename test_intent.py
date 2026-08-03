from core.intent.resolver import IntentResolver

resolver = IntentResolver()

frases = [

    "mostra o contador",

    "qual o pagecount",

    "quantas paginas",

    "estado",

    "status",

    "serial",

    "produto"

]

for frase in frases:

    print()

    print(frase)

    print(

        resolver.resolve(frase)

    )