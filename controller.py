from modules.discovery import discover_printers
from modules.inventory import load_inventory


class Controller:

    def __init__(self):

        self.current_device = None

    def discovery(self):

        return discover_printers()

    async def inventory(self, device):

        self.current_device = await load_inventory(device)

        return self.current_device