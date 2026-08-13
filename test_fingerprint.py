from fingerprint.fingerprint import Fingerprint

fp = Fingerprint(

    model="Lexmark MX611de",

    serial="123ABC",

    firmware="LW71.P635",

    memory=524288,

    pagecount=137974,

    vendor="Lexmark"

)

print(fp)

print()

print(fp.to_dict())