import requests


def executar_post(
    url,
    dados
):

    print("=" * 60)
    print("EXECUTANDO POST")
    print("=" * 60)

    print("URL:")
    print(url)

    print()

    print("DADOS:")
    print(dados)


    try:

        r = requests.post(
            url,
            data=dados,
            timeout=15
        )


        print()

        print("STATUS:")
        print(r.status_code)


        print()

        print("RESPOSTA:")
        print(r.text[:500])


        return r



    except Exception as e:

        print()

        print(
            "ERRO:",
            e
        )

        return None





if __name__ == "__main__":


    url = input(
        "URL POST: "
    )


    campo = input(
        "Campo: "
    )


    valor = input(
        "Valor: "
    )


    executar_post(
        url,
        {
            campo: valor
        }
    )