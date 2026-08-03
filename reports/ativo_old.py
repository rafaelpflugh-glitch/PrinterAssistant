"""
Relatório de Ativo

Etiqueta 100x150
"""

from reports.engine import ReportEngine


class RelatorioAtivo:

    def __init__(self):

        self.engine = ReportEngine()

    def gerar(self, impressora):

        fabricante = impressora.fabricante
        modelo = impressora.modelo()
        serial = impressora.serial
        contador = impressora.contador

        tspl = f"""
SIZE 100 mm,150 mm
GAP 3 mm,0
DIRECTION 1
CLS

TEXT 250,40,"4",0,1,1,"RELATORIO DE ATIVO"

BAR 40,100,700,3

TEXT 40,150,"4",0,1,1,"{fabricante}"

TEXT 40,220,"4",0,1,1,"{modelo}"

TEXT 40,320,"3",0,1,1,"SERIAL"

BARCODE 40,360,"128",120,1,0,3,3,"{serial}"

TEXT 40,500,"3",0,1,1,"{serial}"

TEXT 40,620,"3",0,1,1,"CONTADOR"

TEXT 40,670,"4",0,1,1,"{contador:,}".replace(",",".")

PRINT 1
"""

        return tspl

    def imprimir(self, impressora):

        tspl = self.gerar(impressora)

        self.engine.imprimir(tspl)