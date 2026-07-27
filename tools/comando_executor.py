import requests

from core.comandos_db import carregar



def executar_comando(ip, nome_comando):


    comando = carregar(nome_comando)


    if not comando:


        return {

            "sucesso": False,

            "erro": "Comando não encontrado"

        }



    metodo = comando["metodo"]

    endpoint = comando["endpoint"]


    url = f"http://{ip}{endpoint}"



    try:


        if metodo == "GET":


            resposta = requests.get(
                url,
                timeout=8
            )


        else:


            resposta = requests.post(
                url,
                timeout=8
            )



        return {


            "sucesso": resposta.status_code == 200,

            "status": resposta.status_code,

            "resposta": resposta.text[:500]


        }



    except Exception as erro:


        return {


            "sucesso": False,

            "erro": str(erro)

        }