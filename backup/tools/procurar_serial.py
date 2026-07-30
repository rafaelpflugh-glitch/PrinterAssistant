import os

PASTA="ews_dump"

PALAVRAS=[

"serial",

"serialnumber",

"device serial",

"machineserial",

"printer serial"

]

for raiz,_,arquivos in os.walk(PASTA):

    for arquivo in arquivos:

        caminho=os.path.join(raiz,arquivo)

        try:

            texto=open(
                caminho,
                encoding="utf8",
                errors="ignore"
            ).read().lower()

            for palavra in PALAVRAS:

                if palavra in texto:

                    print("="*80)
                    print(caminho)

                    pos=texto.find(palavra)

                    print(texto[pos-400:pos+900])

                    break

        except:
            pass