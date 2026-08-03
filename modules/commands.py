from pjl.client import PJLClient
from pjl import commands


class PrinterCommands:

    def __init__(self, session):

        self.session = session

        self.pjl = PJLClient(session.ip)


    def info_id(self):

        return self.pjl.send(
            commands.INFO_ID
        )


    def status(self):

        return self.pjl.send(
            commands.INFO_STATUS
        )


    def pagecount(self):

        return self.pjl.send(
            commands.INFO_PAGECOUNT
        )


    def memory(self):

        return self.pjl.send(
            commands.INFO_MEMORY
        )


    def filesystem(self):

        return self.pjl.send(
            commands.INFO_FILESYS
        )


    def variables(self):

        return self.pjl.send(
            commands.INFO_VARIABLES
        )


    def config(self):

        return self.pjl.send(
            commands.INFO_CONFIG
        )


    def echo(self):

        return self.pjl.send(
            commands.ECHO
        )