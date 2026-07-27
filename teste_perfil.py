from core.printer_profile import PrinterProfile



perfil = PrinterProfile(

    "192.168.14.134"

)



dados = {


    "ip":

    "192.168.14.134",


    "fabricante":

    "Lexmark",


    "modelo":

    "MX611",


    "serial":

    "701644HH03ND3",


    "firmware":

    "LW70.SB7.P022",



    "configuracao":

    {

        "Idioma":

        "Português",


        "Duplex":

        "Desativado",


        "Copias":

        "1",


        "Timeout":

        "90"

    }

}



arquivo = perfil.salvar(dados)



print()

print("==============================")

print("PERFIL CRIADO")

print("==============================")

print(arquivo)