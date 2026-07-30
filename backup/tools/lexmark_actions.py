from core.comandos_db import carregar
import requests



def executar_comando(ip, comando):

    dados = carregar(comando)


    if not dados:

        return {

            "sucesso": False,
            "erro": f"Comando não encontrado: {comando}"

        }


    metodo = dados.get("metodo")
    endpoint = dados.get("endpoint")


    url = f"http://{ip}{endpoint}"


    try:


        if metodo == "GET":

            resposta = requests.get(
                url,
                timeout=8
            )


        elif metodo == "POST":

            resposta = requests.post(
                url,
                timeout=8
            )


        else:

            return {

                "sucesso":False,
                "erro":"Método inválido"

            }



        return {

            "sucesso": resposta.status_code == 200,
            "status": resposta.status_code,
            "texto": resposta.text[:300]

        }



    except Exception as erro:


        return {

            "sucesso":False,
            "erro":str(erro)

        }