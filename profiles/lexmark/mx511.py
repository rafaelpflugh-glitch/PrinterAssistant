from profiles.lexmark.common import LexmarkProfile


class MX511Profile(LexmarkProfile):

    modelo = "Lexmark MX511"

    familia = "MX"

    adf = True

    duplex = True

    scanner = True

    fax = True

    color = False