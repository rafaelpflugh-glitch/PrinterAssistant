import zipfile
import os


jar="data/vncviewer.jar"

saida="data/vnc_extract"


os.makedirs(
    saida,
    exist_ok=True
)


with zipfile.ZipFile(jar) as z:

    z.extractall(saida)


print("Extraído em:")
print(saida)