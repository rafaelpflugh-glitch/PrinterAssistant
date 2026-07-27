from core.contexto import obter_contexto



def mostrar_status():


    contexto = obter_contexto()



    if not contexto.get("ip"):


        return """

Nenhuma impressora selecionada.

Use:

procurar impressoras

"""



    return f"""

================================

       IMPRESSORA ATUAL

================================


IP:

{contexto.get('ip')}



Modelo:

{contexto.get('modelo')}



Serial:

{contexto.get('serial')}



Firmware:

{contexto.get('firmware')}



Último diagnóstico:

{contexto.get('ultimo_diagnostico')}



Suprimentos:

{contexto.get('suprimentos')}



================================

"""