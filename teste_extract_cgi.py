import re


arquivo = "data/deviceinfo.html"


with open(
    arquivo,
    encoding="utf-8",
    errors="ignore"
) as f:

    html = f.read()



print()
print("==============================")
print("CGI ENCONTRADOS")
print("==============================")


encontrados = re.findall(
    r'[/\w\-.]+cgi-bin[/\w\-.?=&]+',
    html
)



for item in sorted(set(encontrados)):

    print(item)



print()

print("==============================")
print("TAMANHO HTML")
print("==============================")

print(
    len(html)
)