"""
Printer Assistant
Biblioteca oficial de comandos PJL
Lexmark
"""

# ==========================================================
# INFO
# ==========================================================

INFO_ID = "@PJL INFO ID"

INFO_STATUS = "@PJL INFO STATUS"

INFO_MEMORY = "@PJL INFO MEMORY"

INFO_FILESYS = "@PJL INFO FILESYS"

INFO_PAGECOUNT = "@PJL INFO PAGECOUNT"

INFO_CONFIG = "@PJL INFO CONFIG"

INFO_VARIABLES = "@PJL INFO VARIABLES"

INFO_PRODINFO = "@PJL INFO PRODINFO"

# ==========================================================
# USTATUS
# ==========================================================

USTATUS_DEVICE = "@PJL USTATUS DEVICE = ON"

USTATUS_PAGE = "@PJL USTATUS PAGE = ON"

USTATUS_JOB = "@PJL USTATUS JOB = ON"

USTATUS_OFF = "@PJL USTATUSOFF"

# ==========================================================
# RESET
# ==========================================================

RESET = "@PJL RESET"

INITIALIZE = "@PJL INITIALIZE"

# ==========================================================
# JOB
# ==========================================================

JOB = "@PJL JOB"

EOJ = "@PJL EOJ"

# ==========================================================
# DEFAULT
# ==========================================================

DEFAULTS = "@PJL DEFAULT"

# ==========================================================
# FILESYSTEM
# ==========================================================

FSDIRLIST = '@PJL FSDIRLIST NAME="0:\\"'

FSQUERY = "@PJL FSQUERY"

FSINIT = "@PJL FSINIT"

# ==========================================================
# TEST PAGE
# ==========================================================

TESTPAGE = "@PJL DEFAULT TESTPAGE=ON"

# ==========================================================
# DISPLAY
# ==========================================================

def READY_MESSAGE(text):

    return f'@PJL RDYMSG DISPLAY="{text}"'

# ==========================================================
# ECHO
# ==========================================================

ECHO = "@PJL ECHO PrinterAssistant"

# ==========================================================
# PERSONALITY
# ==========================================================

ENTER_PJL = "\x1B%-12345X"

EXIT_PJL = "\x1B%-12345X"