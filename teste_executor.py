from core.printer import Printer
from core.commands import Commands


printer = Printer("192.168.14.134")

cmd = Commands(printer)

cmd.executar("printer_status")

cmd.executar("print_configuration")

cmd.executar("print_statistics")