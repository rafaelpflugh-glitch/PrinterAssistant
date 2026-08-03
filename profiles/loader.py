from profiles.lexmark.mx611 import MX611Profile
from profiles.lexmark.mx511 import MX511Profile
from profiles.lexmark.ms610 import MS610Profile


def carregar_profile(modelo):

    modelo = modelo.upper()

    if "MX611" in modelo:

        return MX611Profile()

    if "MX511" in modelo:

        return MX511Profile()

    if "MS610" in modelo:

        return MS610Profile()

    return None