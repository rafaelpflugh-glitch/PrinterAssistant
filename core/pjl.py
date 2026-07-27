import socket
import re



IP = "192.168.14.134"

PORTA = 9100



def enviar_pjl(comando):


    dados = b"\033%-12345X"

    dados += comando.encode()

    dados += b"\r\n"

    dados += b"\033%-12345X"



    resposta = b""



    try:


        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )


        sock.settimeout(5)


        sock.connect(
            (IP, PORTA)
        )


        sock.send(
            dados
        )


        while True:


            parte = sock.recv(4096)


            if not parte:

                break


            resposta += parte



        sock.close()



    except Exception as e:

        print(
            "Erro PJL:",
            e
        )



    return resposta.decode(
        "latin1",
        errors="ignore"
    )




def coletar_identificacao():


    resultado = {


        "modelo":
        None,


        "serial":
        None,


        "contador":
        None


    }



    id_resp = enviar_pjl(
        "@PJL INFO ID"
    )


    page_resp = enviar_pjl(
        "@PJL INFO PAGECOUNT"
    )


    config_resp = enviar_pjl(
        "@PJL INFO CONFIG"
    )



    # MODELO

    modelo = re.search(
        r'"(.+?)"',
        id_resp
    )


    if modelo:

        resultado["modelo"] = modelo.group(1)



    # CONTADOR

    contador = re.search(
        r'PAGECOUNT\s+(\d+)',
        page_resp
    )


    if contador:

        resultado["contador"] = int(
            contador.group(1)
        )



    # SERIAL

    serial = re.search(
        r'SERIAL NUMBER=(\S+)',
        config_resp
    )


    if serial:

        resultado["serial"] = serial.group(1)



    return resultado