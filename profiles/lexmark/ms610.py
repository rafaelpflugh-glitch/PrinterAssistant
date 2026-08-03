from profiles.lexmark.common import LexmarkProfile


class MS610Profile(LexmarkProfile):

    modelo = "Lexmark MS610"

    familia = "MS"

    adf = False

    duplex = True

    scanner = False

    fax = False

    color = False