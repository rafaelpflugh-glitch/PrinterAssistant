import os
import re

PASTA="ews_dump"

for raiz,_,arquivos in os.walk(PASTA):

    for arq in arquivos:

        caminho=os.path.join(raiz,arq)

        try:

            txt=open(
                caminho,
                encoding="utf8",
                errors="ignore"
            ).read()

            encontrados=re.findall(

                r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"',
                txt,
                re.I

            )

            if encontrados:

                print("="*80)
                print(caminho)

                for n,v in encontrados:

                    print(n,"=",v)

        except:
            pass