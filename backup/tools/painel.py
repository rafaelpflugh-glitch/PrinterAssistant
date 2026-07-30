from core.contexto import obter_contexto



def linha():

    return "=" * 57



def campo(nome, valor):

    if valor is None:

        valor = "-"

    return f"{nome:.<20}{valor}"



def verificar_porta(texto, porta):


    if not texto:

        return "-"


    texto = texto.lower()


    if str(porta) in texto and "aberta" in texto:

        return "OK"


    return "-"





def painel():


    contexto = obter_contexto()


    if not contexto:


        return """

Nenhuma impressora selecionada.

Use:

procurar

"""



    suprimentos = contexto.get(
        "suprimentos",
        {}
    )


    toner = suprimentos.get(
        "toner",
        {}
    )


    imagem = suprimentos.get(
        "imagem",
        {}
    )



    diagnostico = contexto.get(
        "ultimo_diagnostico",
        ""
    )



    return f"""

{linha()}
              PRINTER ASSISTANT V0.1
{linha()}


{campo("MODELO", contexto.get("modelo"))}

{campo("SERIAL", contexto.get("serial"))}

{campo("FIRMWARE", contexto.get("firmware"))}

{campo("IP", contexto.get("ip"))}



{linha()}
SUPRIMENTOS
{linha()}


TONER


{campo("Serial", toner.get("serial"))}

{campo("Chip", toner.get("chip"))}

{campo("Nível", toner.get("nivel")+"%" if toner.get("nivel") else "-")}

{campo("Páginas", toner.get("paginas"))}

{campo("Restante", toner.get("restante"))}

{campo("Capacidade", toner.get("capacidade"))}



---------------------------------------------------------


UNIDADE DE IMAGEM


{campo("Serial", imagem.get("serial"))}

{campo("Nível", imagem.get("nivel")+"%" if imagem.get("nivel") else "-")}

{campo("Páginas", imagem.get("paginas"))}



{linha()}
REDE
{linha()}


HTTP................. {verificar_porta(diagnostico,"80")}

HTTPS................ {verificar_porta(diagnostico,"443")}

RAW 9100............. {verificar_porta(diagnostico,"9100")}

LPR.................. {verificar_porta(diagnostico,"515")}

IPP.................. {verificar_porta(diagnostico,"631")}



{linha()}
ÚLTIMA AÇÃO
{linha()}


{contexto.get("ultima_acao","Nenhuma")}



{linha()}

"""