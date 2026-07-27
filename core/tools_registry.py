from tools.network import testar
from tools.printer import coletar_debug
from tools.diagnostico import diagnosticar
from tools.ews import explorar
from tools.usb import diagnostico_usb

from tools.lexmark_reset import (
    reset_impressora,
    reset_rede,
    reset_apps
)

from tools.lexmark_config import (
    pagina_demonstracao,
    relatorio_ativo,
    pagina_configuracao,
    configurar_papel_pesado,
    configurar_textura_aspero
)

from tools.discovery import procurar



# ==================================================
# REGISTRO DE FERRAMENTAS
# ==================================================


FERRAMENTAS = {



"procurar":
{
    "descricao":
    """
Procura impressoras Lexmark na rede.

Não necessita IP.
""",

    "funcao":
    procurar,

    "argumentos":
    "nenhum"
},





"teste_rede":
{
    "descricao":
    """
Testa comunicação de rede.
Entrada: IP
""",

    "funcao":
    testar,

    "argumentos":
    "ip"
},





"coletar_debug":
{
    "descricao":
    """
Coleta SysDebugData Lexmark.

Retorna:
- modelo
- serial
- firmware
- suprimentos

Entrada:
IP
""",

    "funcao":
    coletar_debug,

    "argumentos":
    "ip"
},





"diagnostico":
{
    "descricao":
    """
Executa diagnóstico inicial.

Entrada:
IP
""",

    "funcao":
    diagnosticar,

    "argumentos":
    "ip"
},





"explorar_ews":
{
    "descricao":
    """
Explora páginas EWS.

Entrada:
IP
""",

    "funcao":
    explorar,

    "argumentos":
    "ip"
},





"usb":
{
    "descricao":
    """
Teste USB local.
""",

    "funcao":
    diagnostico_usb,

    "argumentos":
    "nenhum"
},





"pagina_demonstracao":
{
    "descricao":
    """
Solicita impressão da página demonstração.

Entrada:
IP
""",

    "funcao":
    pagina_demonstracao,

    "argumentos":
    "ip"
},





"relatorio_ativo":
{
    "descricao":
    """
Solicita relatório de ativos.

Entrada:
IP
""",

    "funcao":
    relatorio_ativo,

    "argumentos":
    "ip"
},





"pagina_configuracao":
{
    "descricao":
    """
Solicita página de configuração.

Entrada:
IP
""",

    "funcao":
    pagina_configuracao,

    "argumentos":
    "ip"
},





"papel_pesado":
{
    "descricao":
    """
Configura papel pesado.

Entrada:
IP
""",

    "funcao":
    configurar_papel_pesado,

    "argumentos":
    "ip"
},





"textura_aspera":
{
    "descricao":
    """
Configura textura áspera.

Entrada:
IP
""",

    "funcao":
    configurar_textura_aspero,

    "argumentos":
    "ip"
},





"reset_impressora":
{
    "descricao":
    """
Reset completo.

Somente autorizado.

Entrada:
IP
""",

    "funcao":
    reset_impressora,

    "argumentos":
    "ip"
},





"reset_rede":
{
    "descricao":
    """
Reset rede.

Entrada:
IP
""",

    "funcao":
    reset_rede,

    "argumentos":
    "ip"
},





"reset_apps":
{
    "descricao":
    """
Reset aplicações Lexmark.

Entrada:
IP
""",

    "funcao":
    reset_apps,

    "argumentos":
    "ip"
}

}






# ==================================================
# MOSTRA PARA HERMES
# ==================================================

def listar_ferramentas():


    texto = ""


    for nome, dados in FERRAMENTAS.items():


        texto += f"""

FERRAMENTA:

{nome}


ENTRADA:

{dados['argumentos']}


DESCRIÇÃO:

{dados['descricao']}


----------------------------

"""


    return texto






# ==================================================
# EXECUTOR
# ==================================================

def executar(nome,*args):


    if nome not in FERRAMENTAS:

        return (
            f"Ferramenta {nome} inexistente."
        )


    funcao = FERRAMENTAS[nome]["funcao"]


    try:

        return funcao(*args)


    except Exception as erro:

        return (
            "Erro executando ferramenta:\n"
            + str(erro)
        )