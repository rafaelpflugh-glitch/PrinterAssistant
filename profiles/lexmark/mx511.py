from profiles.lexmark.common import LexmarkProfile


class MX511Profile(LexmarkProfile):

    model = "MX511"

    family = "Lexmark MX"

    capabilities = [

        "mono",

        "scanner",

        "duplex",

        "network",

        "fax",

        "adf"

    ]

    supported_commands = [

        "pagecount",

        "status",

        "memory",

        "config",

        "variables",

        "prodinfo"

    ]