from core.session import Session

from core.session_loader import SessionLoader

from fingerprint.fingerprint import Fingerprint


sessao = Session()

sessao.connect("192.168.0.55")


fp = Fingerprint(

    model="Lexmark MX611de",

    serial="123ABC",

    firmware="LW71.P635",

    memory=524288,

    pagecount=137974,

    vendor="Lexmark"

)


SessionLoader.load(

    sessao,

    fp

)


print()

print(sessao.info())