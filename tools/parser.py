import json


OID_MAP = {

    "modelo":
    "1.3.6.1.4.1.641.2.1.2.1.2.1",

    "serial":
    "1.3.6.1.4.1.641.2.1.2.1.6.1",

    "firmware":
    "1.3.6.1.4.1.641.2.1.2.1.4.1",

}


def limpar(valor):

    return (
        valor
        .replace("\x00", "")
        .strip()
    )


def parse_dump(caminho):

    dados = {}


    with open(
        caminho,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as arquivo:


        for linha in arquivo:

            if "=" not in linha:
                continue


            oid, valor = linha.split(
                "=",
                1
            )


            oid = oid.strip()
            valor = limpar(valor)


            for nome, alvo in OID_MAP.items():

                if oid == alvo:

                    dados[nome] = valor


    dados["marca"] = "Lexmark"


    return dados



if __name__ == "__main__":


    resultado = parse_dump(
        "../dumps/mx611.txt"
    )


    print(
        json.dumps(
            resultado,
            indent=4,
            ensure_ascii=False
        )
    )