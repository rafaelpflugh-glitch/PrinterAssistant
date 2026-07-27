from core.executor import executor


INFO = {

    "id":1,

    "nome":"Página Configuração"

}


def executar():

    resposta = executor.executar(
        "print_config"
    )

    print()

    print("="*60)

    print(resposta.text[:4000])

    input("\nENTER...")