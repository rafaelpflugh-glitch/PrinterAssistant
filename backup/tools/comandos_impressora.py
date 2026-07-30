from core.contexto import obter_contexto

from tools.lexmark_actions import executar_comando



def comando_impressora(comando):


    contexto = obter_contexto()


    ip = contexto.get("ip")


    if not ip:

        return "Nenhuma impressora selecionada."



    mapa = {


        "pagina configuração":
        "pagina_configuracao",


        "pagina demonstracao":
        "pagina_demo",


        "pagina ativos":
        "pagina_ativos",


        "pagina menus":
        "pagina_menus",


        "papel pesado":
        "papel_pesado",


        "papel normal":
        "papel_normal",


        "textura aspera":
        "textura_aspera",


        "textura normal":
        "textura_normal",


        "reset fabrica":
        "reset_factory",


        "reset rede":
        "reset_rede",


        "reset apps":
        "reset_apps",


        "scanner ligar":
        "scanner_on",


        "scanner desligar":
        "scanner_off",


        "reiniciar":
        "reiniciar"

    }



    comando_db = mapa.get(comando)


    if not comando_db:


        return "Comando não encontrado."



    resultado = executar_comando(
        ip,
        comando_db
    )


    return resultado