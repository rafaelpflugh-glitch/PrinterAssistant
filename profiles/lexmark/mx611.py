from profiles.lexmark.common import LexmarkProfile


class MX611Profile(LexmarkProfile):

    model = "MX611"

    family = "Lexmark MX"

    capabilities = [

        "mono",

        "scanner",

        "duplex",

        "network",

        "fax",

        "adf",

        "touch"

    ]

    supported_commands = [

        "pagecount",

        "status",

        "memory",

        "config",

        "variables",

        "prodinfo"

    ]