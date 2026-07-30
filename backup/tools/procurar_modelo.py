import os

PASTA = "ews_dump"

PALAVRAS = [

    "model",
    "modelname",
    "device model",
    "printer model",
    "serial",
    "serialnumber",
    "hostname",
    "firmware",
    "version",
    "machine type",
    "deviceinfo"

]

for raiz, _, arquivos in os.walk(PASTA):

    for arquivo in arquivos:

        caminho = os.path.join(raiz, arquivo)

        try:

            with open(
                caminho,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                texto = f.read().lower()

            for palavra in PALAVRAS:

                if palavra in texto:

                    print("=" * 80)
                    print(caminho)
                    print()

                    pos = texto.find(palavra)

                    ini = max(0, pos - 500)

                    fim = pos + 1200

                    print(texto[ini:fim])

                    break

        except:
            pass