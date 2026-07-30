from tools.bancada.procedimentos import abrir


COMANDOS = {

    "troca iu":
        "troca_iu",

    "troca toner":
        "troca_toner",

    "teste usb":
        "teste_usb",

    "teste rede":
        "teste_rede",

    "teste impressão":
        "teste_impressao",

    "scanner":
        "scanner",

    "fax":
        "fax"

}


def interpretar(texto):

    texto = texto.lower()

    for chave, procedimento in COMANDOS.items():

        if chave in texto:

            return abrir(procedimento)

    return None