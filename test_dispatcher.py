from core.session import PrinterSession

from core.intent.resolver import IntentResolver

from core.dispatcher import Dispatcher


print()

print("=" * 60)

print("TESTE DISPATCHER")

print("=" * 60)


sessao = PrinterSession()

sessao.carregar()


resolver = IntentResolver()

dispatcher = Dispatcher(sessao)


texto = "mostra o contador"


intent = resolver.resolve(texto)


print()

print("Intent:")

print(intent)


resultado = dispatcher.dispatch(intent)


print()

print("Resultado:")

print(resultado)