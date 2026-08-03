"""
============================================================
Printer Assistant
Biblioteca oficial de comandos PJL
Compatível Lexmark
============================================================
"""


# ==========================================================
# ENTER / EXIT PJL
# ==========================================================

ENTER_PJL = "\x1B%-12345X"

EXIT_PJL = "\x1B%-12345X"



# ==========================================================
# IDENTIFICAÇÃO
# ==========================================================

INFO_ID = (
    "@PJL INFO ID"
)


INFO_PRODINFO = (
    "@PJL INFO PRODINFO"
)



# ==========================================================
# STATUS
# ==========================================================

INFO_STATUS = (
    "@PJL INFO STATUS"
)



INFO_PAGECOUNT = (
    "@PJL INFO PAGECOUNT"
)



INFO_MEMORY = (
    "@PJL INFO MEMORY"
)



INFO_CONFIG = (
    "@PJL INFO CONFIG"
)



INFO_VARIABLES = (
    "@PJL INFO VARIABLES"
)



# ==========================================================
# FILESYSTEM
# ==========================================================

INFO_FILESYS = (
    "@PJL INFO FILESYS"
)



FSDIRLIST = (
    '@PJL FSDIRLIST NAME="0:\\"'
)



FSQUERY = (
    "@PJL FSQUERY"
)



FSINIT = (
    "@PJL FSINIT"
)



# ==========================================================
# STATUS AUTOMÁTICO
# ==========================================================

USTATUS_DEVICE = (
    "@PJL USTATUS DEVICE = ON"
)



USTATUS_PAGE = (
    "@PJL USTATUS PAGE = ON"
)



USTATUS_JOB = (
    "@PJL USTATUS JOB = ON"
)



USTATUS_OFF = (
    "@PJL USTATUSOFF"
)



# ==========================================================
# JOB CONTROL
# ==========================================================

JOB = (
    "@PJL JOB"
)



EOJ = (
    "@PJL EOJ"
)



# ==========================================================
# SISTEMA
# ==========================================================

RESET = (
    "@PJL RESET"
)



INITIALIZE = (
    "@PJL INITIALIZE"
)



DEFAULTS = (
    "@PJL DEFAULT"
)



# ==========================================================
# TESTES / PÁGINAS
# ==========================================================

TESTPAGE = (
    "@PJL DEFAULT TESTPAGE=ON"
)



CONFIG_PAGE = (
    "@PJL INFO CONFIG"
)



SUPPLIES_PAGE = (
    "@PJL INFO SUPPLIES"
)



DIAGNOSTIC_PAGE = (
    "@PJL INFO DIAGNOSTICS"
)



# ==========================================================
# DISPLAY
# ==========================================================

def READY_MESSAGE(text):

    return (
        f'@PJL RDYMSG DISPLAY="{text}"'
    )



def CLEAR_DISPLAY():

    return (
        '@PJL RDYMSG DISPLAY=""'
    )



# ==========================================================
# ECHO
# ==========================================================

ECHO = (
    "@PJL ECHO PrinterAssistant"
)