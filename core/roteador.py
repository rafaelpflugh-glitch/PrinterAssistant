from tools.painel import painel
from tools.bancada import bancada
from tools.analisar import analisar

from tools.printer_selector import procurar
from tools.scanner import escanear_rede

from core.agente import executar

from tools.comandos_impressora import comando_impressora


def executar_comando(texto):


    comando = texto.lower()



    if comando == "painel":

        return painel()



    if comando == "bancada":

        return bancada()



    if comando == "analisar":

        return analisar()



    if comando == "procurar":

        return procurar()



    if comando == "scan":

        return escanear_rede()



    if comando in [

        "pagina configuração",
        "pagina demonstracao",
        "relatorio ativo",
        "reset fabrica",
        "reset rede",
        "reset apps",
        "papel pesado",
        "textura aspera"

    ]:

        return comando_impressora(comando)



    return executar(texto)