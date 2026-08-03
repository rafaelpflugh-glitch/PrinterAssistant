import socket


LABEL_PRINTER_IP = "192.168.14.151"
LABEL_PRINTER_PORT = 9100


class ActiveLabel:

    def __init__(self, device):

        self.device = device


    def zpl(self):

        dados = self.device.to_dict()

        ident = dados.get("identificacao", {})

        modelo = ident.get("modelo", "DESCONHECIDO")
        serial = ident.get("serial", "SEM SERIAL")
        contador = ident.get("contador", 0)

        zpl = f"""
^XA

^CF0,30

^FO30,30^FD{modelo}^FS

^CF0,25

^FO30,80^FDSerial:^FS

^BY2,2,70

^FO30,115^BCN,70,Y,N,N

^FD{serial}^FS

^CF0,25

^FO30,240^FDContador: {contador}^FS

^XZ
"""

        return zpl


    def imprimir(self):

        zpl = self.zpl()

        s = socket.socket()

        s.settimeout(5)

        s.connect(
            (
                LABEL_PRINTER_IP,
                LABEL_PRINTER_PORT
            )
        )

        s.sendall(
            zpl.encode("utf-8")
        )

        s.close()

        return True