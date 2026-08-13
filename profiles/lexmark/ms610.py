from profiles.lexmark.common import LexmarkProfile


class MS610Profile(LexmarkProfile):

    model = "MS610"

    family = "Lexmark MS"

    capabilities = [

        "mono",

        "duplex",

        "network",

        "usb",

        "manual_tray"

    ]

    supported_commands = [

        "pagecount",

        "status",

        "memory",

        "config",

        "variables",

        "prodinfo"

    ]