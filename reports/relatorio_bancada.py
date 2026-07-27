import json
from datetime import datetime


# ==========================================
# CARREGAR DADOS
# ==========================================

with open(
    "printer_data.json",
    "r",
    encoding="utf-8"
) as arquivo:

    dados = json.load(arquivo)



# ==========================================
# GERAR RELATÓRIO HTML
# ==========================================


html = f"""

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
Printer Assistant
</title>


<style>

body {{

    font-family: Arial;
    margin:40px;
    background:#f4f4f4;

}}


.card {{

    background:white;
    padding:25px;
    border-radius:10px;
    margin-bottom:20px;

}}


h1 {{

    color:#222;

}}


table {{

    width:100%;
    border-collapse:collapse;

}}


th {{

    background:#333;
    color:white;
    padding:10px;

}}


td {{

    padding:10px;
    border-bottom:1px solid #ddd;

}}


.BOM {{

    color:green;
    font-weight:bold;

}}


.ATENCAO {{

    color:orange;
    font-weight:bold;

}}


.BAIXO {{

    color:red;
    font-weight:bold;

}}


.barra {{

    background:#ddd;
    width:100%;
    height:20px;

}}


.progresso {{

    height:20px;
    background:#4caf50;

}}


</style>


</head>



<body>


<div class="card">


<h1>
PRINTER ASSISTANT
</h1>


<h2>
Identificação da Máquina
</h2>


<p>
<b>Modelo:</b>
{dados["identificacao"]["modelo"]}
</p>


<p>
<b>Serial:</b>
{dados["identificacao"]["serial"]}
</p>


<p>
<b>Contador:</b>
{dados["identificacao"]["contador"]:,}
</p>


<p>
<b>IP:</b>
{dados["ip"]}
</p>


<p>
<b>Data:</b>
{dados["data"]}
</p>


</div>




<div class="card">


<h2>
Suprimentos
</h2>



<table>


<tr>

<th>
Item
</th>

<th>
Capacidade
</th>

<th>
Restante
</th>

<th>
Consumido
</th>

<th>
Nível
</th>

<th>
Status
</th>

</tr>


"""



for s in dados["supplies"]:


    html += f"""


<tr>

<td>
{s["nome"]}
</td>


<td>
{s["capacidade"]:,}
</td>


<td>
{s["restante"]:,}
</td>


<td>
{s["consumido"]:,}
</td>


<td>


<div class="barra">

<div class="progresso"

style="width:{s["nivel"]}%">

</div>

</div>


{s["nivel"]}%


</td>


<td class="{s["status"]}">

{s["status"]}

</td>


</tr>


"""



html += """

</table>


</div>


</body>

</html>

"""



# ==========================================
# SALVAR
# ==========================================


arquivo_saida = "relatorio_bancada.html"


with open(

    arquivo_saida,

    "w",

    encoding="utf-8"

) as arquivo:


    arquivo.write(html)



print()

print("="*50)

print("RELATÓRIO GERADO")

print("="*50)

print()

print(arquivo_saida)