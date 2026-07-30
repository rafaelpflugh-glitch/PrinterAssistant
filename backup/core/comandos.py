from tools.painel import painel
from tools.bancada import bancada
from tools.analise_tecnica import analisar_resultados
from tools.actions.impressao import imprimir
from tools.actions.reset import executar_reset
from tools.actions.usb import testar_usb
from tools.actions.papel import alterar_papel

from core.contexto import obter_contexto


def executar(comando):

    comando = comando.lower().strip()

    contexto = obter_contexto()

    ip = contexto.get("ip")

    if comando == "painel":

        return painel()

    if comando == "bancada":

        return bancada()

    if comando == "analisar":

        return analisar_resultados(contexto)

    if comando == "usb":

        return testar_usb(ip)

    if comando == "pagina configuracao":

        return imprimir(ip, "config")

    if comando == "pagina menus":

        return imprimir(ip, "menus")

    if comando == "pagina demonstracao":

        return imprimir(ip, "demo")

    if comando == "relatorio ativo":

        return imprimir(ip, "asset")

    if comando == "reset fabrica":

        return executar_reset(ip, "reset")

    if comando == "reset rede":

        return executar_reset(ip, "reset_rede")

    if comando == "reset apps":

        return executar_reset(ip, "apps")

    return None