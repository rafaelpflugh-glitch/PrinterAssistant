"""
Printer Assistant
Lexmark PJL Command Catalog

Todos os comandos PJL conhecidos da Lexmark
ficam centralizados aqui.
"""


# ==========================
# CONSULTAS
# ==========================

INFO_ID = "@PJL INFO ID"

INFO_STATUS = "@PJL INFO STATUS"

INFO_PAGECOUNT = "@PJL INFO PAGECOUNT"

INFO_MEMORY = "@PJL INFO MEMORY"

INFO_CONFIG = "@PJL INFO CONFIG"

INFO_VARIABLES = "@PJL INFO VARIABLES"


# ==========================
# MENSAGENS
# ==========================

def display(text):

    return f'@PJL RDYMSG DISPLAY="{text}"'


# ==========================
# RESET
# ==========================

INITIALIZE = "@PJL INITIALIZE"

RESET = "@PJL RESET"


# ==========================
# JOB
# ==========================

JOB = "@PJL JOB"

EOJ = "@PJL EOJ"


# ==========================
# USTATUS
# ==========================

USTATUS_ON = "@PJL USTATUS DEVICE = ON"

USTATUS_OFF = "@PJL USTATUS DEVICE = OFF"


# ==========================
# TEST PAGE
# ==========================

TEST_PAGE = "@PJL DEFAULT TESTPAGE=ON"