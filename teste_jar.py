import zipfile


arquivo="data/vncviewer.jar"


print("==============================")
print("CONTEUDO JAR")
print("==============================")


with zipfile.ZipFile(arquivo) as z:

    for item in z.namelist():

        print(item)