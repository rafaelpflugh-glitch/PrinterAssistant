import asyncio
import sys
from pathlib import Path


# ============================================================
# PRINTER ASSISTANT - MAIN
# ============================================================
#
# Ponto de entrada principal do sistema.
#
# O MAIN coordena os módulos.
#
# Comunicação específica:
#
#   core.scanner
#   core.pjl
#   core.snmp
#   core.device
#   core.session
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# IMPORTS
# ============================================================

from core.scanner import descobrir_rede

from core.device import PrinterDevice

from core.session import PrinterSession

from core.pjl import PJLPrinter


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_tela():

    if sys.platform.startswith("win"):

        import os

        os.system("cls")

    else:

        import os

        os.system("clear")


def pausa():

    print()

    input(
        "Pressione ENTER para continuar..."
    )


def linha():

    print(
        "=" * 68
    )


def titulo(texto):

    print()

    linha()

    print(
        texto.center(68)
    )

    linha()

    print()


def formatar_numero(valor):

    if valor is None:

        return "desconhecido"

    try:

        return f"{int(valor):,}".replace(
            ",",
            "."
        )

    except Exception:

        return str(valor)


# ============================================================
# DESCOBRIR IP DO COMPUTADOR + REDE
# ============================================================

def normalizar_rede(resultado):

    """
    O scanner pode retornar:

        "192.168.14.0/24"

    ou:

        ("192.168.14.165", "192.168.14.0/24")

    Esta função normaliza os dois formatos.
    """

    ip_computador = None
    rede = None


    if isinstance(
        resultado,
        tuple
    ):

        if len(resultado) >= 2:

            ip_computador = resultado[0]

            rede = resultado[1]

        elif len(resultado) == 1:

            rede = resultado[0]


    else:

        rede = resultado


    return (
        ip_computador,
        rede
    )


# ============================================================
# IDENTIFICAÇÃO PJL RÁPIDA
# ============================================================
#
# ATENÇÃO:
#
# NÃO usamos PrinterDevice.coletar() aqui.
#
# Essa função faz coleta completa:
#
#   PJL
#   contador
#   SNMP
#   suprimentos
#
# Para a tela de seleção precisamos somente do modelo.
#
# Portanto usamos diretamente:
#
#   @PJL INFO ID
#
# que é muito mais rápido.
#
# ============================================================

async def identificar_pjl_rapido(ip):

    def executar():

        try:

            impressora = PJLPrinter(

                ip=ip,

                timeout=1.5

            )


            resposta = impressora.info_id()


            if not resposta:

                return None


            modelo = (
                PJLPrinter._extrair_modelo(
                    resposta
                )
            )


            if not modelo:

                return None


            return modelo


        except Exception:

            return None


    try:

        modelo = await asyncio.wait_for(

            asyncio.to_thread(
                executar
            ),

            timeout=2.5

        )


    except asyncio.TimeoutError:

        return None


    except Exception:

        return None


    return modelo


# ============================================================
# IDENTIFICAÇÃO DO EQUIPAMENTO
# ============================================================

async def identificar_equipamento(ip):

    """
    Faz somente a identificação necessária para
    apresentar o equipamento ao técnico.

    NÃO executa coleta completa.
    """

    modelo = await identificar_pjl_rapido(
        ip
    )


    if modelo:

        device = PrinterDevice(
            ip=ip
        )


        fabricante = (
            device.detectar_fabricante(
                modelo
            )
        )


        familia = (
            device.detectar_familia(
                modelo
            )
        )


        tipo = (
            device.detectar_tipo(
                fabricante,
                modelo
            )
        )


        return {

            "ip": ip,

            "fabricante": fabricante,

            "modelo": modelo,

            "familia": familia,

            "tipo": tipo,

            "identificado": True

        }


    return {

        "ip": ip,

        "fabricante": "Desconhecido",

        "modelo": "Equipamento não identificado",

        "familia": "",

        "tipo": "",

        "identificado": False

    }


# ============================================================
# TESTAR RAW 9100
# ============================================================

async def testar_raw(ip):

    try:

        reader, writer = await asyncio.wait_for(

            asyncio.open_connection(

                ip,

                9100

            ),

            timeout=0.45

        )


        writer.close()


        try:

            await writer.wait_closed()

        except Exception:

            pass


        return ip


    except Exception:

        return None


# ============================================================
# DESCOBERTA DE IMPRESSORAS
# ============================================================

async def descobrir_impressoras():

    limpar_tela()

    titulo(
        "DESCOBERTA DE IMPRESSORAS"
    )


    print(
        "Descobrindo equipamentos de impressão..."
    )

    print()


    # ========================================================
    # DESCOBRIR REDE
    # ========================================================

    try:

        resultado_rede = descobrir_rede()

    except Exception as erro:

        print(
            "Erro ao descobrir rede:",
            erro
        )

        pausa()

        return None


    ip_computador, rede = (
        normalizar_rede(
            resultado_rede
        )
    )


    if not rede:

        print(
            "Não foi possível determinar a rede local."
        )

        pausa()

        return None


    print(
        "IP deste computador:",
        ip_computador
        if ip_computador
        else "desconhecido"
    )


    print(
        "Rede local:",
        rede
    )


    print()


    # ========================================================
    # IPADDRESS
    # ========================================================

    import ipaddress


    try:

        rede_obj = ipaddress.ip_network(

            rede,

            strict=False

        )

    except Exception as erro:

        print(
            "Erro ao interpretar a rede:",
            erro
        )

        pausa()

        return None


    # ========================================================
    # ARP
    # ========================================================

    print(
        "Consultando tabela ARP..."
    )

    print()


    ips_ativos = []


    try:

        import subprocess


        resultado = subprocess.run(

            [
                "arp",
                "-a"
            ],

            capture_output=True,

            text=True,

            encoding="cp850",

            errors="replace",

            timeout=5

        )


        for linha_arp in resultado.stdout.splitlines():

            linha_arp = linha_arp.strip()


            if not linha_arp:

                continue


            partes = linha_arp.split()


            if not partes:

                continue


            candidato = partes[0]


            try:

                ip_obj = ipaddress.ip_address(
                    candidato
                )

            except ValueError:

                continue


            if ip_obj in rede_obj:

                ips_ativos.append(
                    str(ip_obj)
                )


    except Exception:

        pass


    # ========================================================
    # REMOVER DUPLICADOS
    # ========================================================

    ips_ativos = sorted(

        set(
            ips_ativos
        ),

        key=lambda valor: tuple(

            int(parte)

            for parte in valor.split(".")

        )

    )


    print(
        f"{len(ips_ativos)} dispositivos conhecidos pela tabela ARP."
    )

    print()


    # ========================================================
    # FALLBACK
    # ========================================================

    if not ips_ativos:

        print(
            "Tabela ARP não forneceu dispositivos."
        )

        print(
            "Usando descoberta pela rede local..."
        )

        print()


        ips_ativos = [

            str(ip)

            for ip in rede_obj.hosts()

        ]


    # ========================================================
    # RAW 9100
    # ========================================================

    print(
        "Testando porta RAW 9100..."
    )

    print()


    tarefas_raw = [

        testar_raw(ip)

        for ip in ips_ativos

    ]


    resultados_raw = await asyncio.gather(

        *tarefas_raw,

        return_exceptions=True

    )


    encontrados = []


    for resultado in resultados_raw:

        if isinstance(
            resultado,
            str
        ):

            encontrados.append(
                resultado
            )


    # ========================================================
    # NENHUM EQUIPAMENTO
    # ========================================================

    if not encontrados:

        print(
            "Nenhum equipamento de impressão encontrado."
        )

        print()

        pausa()

        return None


    # ========================================================
    # IDENTIFICAÇÃO RÁPIDA
    # ========================================================
    #
    # AGORA fazemos somente INFO ID.
    #
    # Não usamos device.coletar().
    #
    # ========================================================

    print(
        "Identificando equipamentos..."
    )

    print(
        "Consultando identificação rápida via PJL..."
    )

    print()


    tarefas_identificacao = [

        identificar_equipamento(ip)

        for ip in encontrados

    ]


    resultados_identificacao = await asyncio.gather(

        *tarefas_identificacao,

        return_exceptions=True

    )


    equipamentos = []


    for resultado in resultados_identificacao:

        if isinstance(
            resultado,
            dict
        ):

            equipamentos.append(
                resultado
            )


    # ========================================================
    # ORDENAR PELO IP
    # ========================================================

    equipamentos.sort(

        key=lambda item: tuple(

            int(parte)

            for parte in item["ip"].split(".")

        )

    )


    # ========================================================
    # MOSTRAR RESULTADOS
    # ========================================================

    print()

    linha()

    print(
        "IMPRESSORAS ENCONTRADAS"
    )

    linha()

    print()


    for numero, equipamento in enumerate(

        equipamentos,

        start=1

    ):

        fabricante = equipamento.get(
            "fabricante",
            "Desconhecido"
        )


        modelo = equipamento.get(
            "modelo",
            "Equipamento não identificado"
        )


        ip = equipamento.get(
            "ip",
            "desconhecido"
        )


        # ----------------------------------------------------
        # Equipamento identificado
        # ----------------------------------------------------

        if equipamento.get(
            "identificado"
        ):

            print(
                f"[{numero}] {fabricante} {modelo}"
            )

            print(
                f"    IP: {ip}"
            )

            print(
                "    Família:",
                equipamento.get(
                    "familia",
                    ""
                )
            )

            print(
                "    Tipo:",
                equipamento.get(
                    "tipo",
                    ""
                )
            )


        # ----------------------------------------------------
        # Equipamento não identificado
        # ----------------------------------------------------

        else:

            print(
                f"[{numero}] Equipamento de impressão não identificado"
            )

            print(
                f"    IP: {ip}"
            )

            print(
                "    Modelo: não identificado"
            )


        print()


    # ========================================================
    # SELEÇÃO
    # ========================================================

    linha()

    print(
        "SELECIONE A IMPRESSORA"
    )

    linha()

    print()


    while True:

        escolha = input(

            "Digite o número (ou ENTER para cancelar): "

        ).strip()


        if not escolha:

            return None


        try:

            numero = int(
                escolha
            )

        except ValueError:

            print()

            print(
                "Digite um número válido."
            )

            continue


        if not 1 <= numero <= len(
            equipamentos
        ):

            print()

            print(
                "Número fora da lista."
            )

            continue


        equipamento = equipamentos[
            numero - 1
        ]

        break


    # ========================================================
    # EQUIPAMENTO ESCOLHIDO
    # ========================================================

    ip = equipamento[
        "ip"
    ]


    limpar_tela()

    titulo(
        "EQUIPAMENTO SELECIONADO"
    )


    print(
        "Fabricante:",
        equipamento.get(
            "fabricante",
            "Desconhecido"
        )
    )


    print(
        "Modelo:",
        equipamento.get(
            "modelo",
            "Desconhecido"
        )
    )


    print(
        "IP:",
        ip
    )


    print()


    print(
        "Criando dispositivo..."
    )


    device = PrinterDevice(
        ip=ip
    )


    # ========================================================
    # COLETA COMPLETA
    # ========================================================
    #
    # SOMENTE agora.
    #
    # Este é o ponto em que podemos esperar mais tempo.
    #
    # ========================================================

    print(
        "Coletando dados completos..."
    )

    print()


    try:

        await asyncio.wait_for(

            device.coletar(),

            timeout=15

        )


    except asyncio.TimeoutError:

        print(
            "AVISO: a coleta demorou mais que 15 segundos."
        )

        print(
            "O equipamento pode estar respondendo lentamente."
        )

        print()


    except Exception as erro:

        print(
            "AVISO durante a coleta:",
            erro
        )

        print()


    return device


# ============================================================
# SESSÃO
# ============================================================

def ativar_sessao(device):

    sessao = PrinterSession()

    sessao.ativar(
        device
    )

    return sessao


# ============================================================
# EXIBIR IMPRESSORA
# ============================================================

def exibir_impressora(
    device,
    sessao=None
):

    dados = device.to_dict()


    identificacao = dados.get(
        "identificacao",
        {}
    )


    conectividade = dados.get(
        "conectividade",
        {}
    )


    supplies = dados.get(
        "supplies",
        []
    )


    print()

    linha()

    print(
        "IMPRESSORA ATIVA"
    )

    linha()

    print()


    print(
        "Fabricante:",
        identificacao.get(
            "fabricante",
            "Desconhecido"
        )
    )


    print(
        "Modelo:",
        identificacao.get(
            "modelo",
            "Desconhecido"
        )
    )


    print(
        "Família:",
        identificacao.get(
            "familia",
            ""
        )
    )


    print(
        "Tipo:",
        identificacao.get(
            "tipo",
            ""
        )
    )


    print(
        "Serial:",
        identificacao.get(
            "serial",
            "Desconhecido"
        )
    )


    print(
        "Contador:",
        formatar_numero(
            identificacao.get(
                "contador"
            )
        )
    )


    print()

    print(
        "IP:",
        device.ip
    )


    print()


    print(
        "PJL:",
        "ATIVO"
        if conectividade.get("pjl")
        else "INATIVO"
    )


    print(
        "SNMP:",
        "ATIVO"
        if conectividade.get("snmp")
        else "INATIVO"
    )


    print(
        "Estado:",
        dados.get(
            "estado",
            "OFFLINE"
        )
    )


    print(
        "Suprimentos:",
        len(supplies)
    )


# ============================================================
# DIAGNÓSTICO
# ============================================================

async def diagnostico(
    device,
    sessao
):

    limpar_tela()

    titulo(
        "DIAGNÓSTICO"
    )


    print(
        "Atualizando dados da impressora..."
    )

    print()


    try:

        await asyncio.wait_for(

            device.coletar(),

            timeout=15

        )


    except asyncio.TimeoutError:

        print(
            "Aviso: coleta demorou mais de 15 segundos."
        )


    except Exception as erro:

        print(
            "Aviso:",
            erro
        )


    sessao.ativar(
        device
    )


    exibir_impressora(
        device,
        sessao
    )


    print()

    linha()

    print(
        "SUPRIMENTOS"
    )

    linha()


    supplies = device.supplies


    if not supplies:

        print()

        print(
            "Nenhum suprimento encontrado."
        )


    else:

        for numero, item in enumerate(

            supplies,

            start=1

        ):

            print()

            print(
                f"[{numero}]",
                item.get(
                    "nome",
                    "Desconhecido"
                )
            )


            print(
                "    Capacidade:",
                formatar_numero(
                    item.get(
                        "capacidade"
                    )
                )
            )


            print(
                "    Restante:",
                formatar_numero(
                    item.get(
                        "restante"
                    )
                )
            )


            print(
                "    Consumido:",
                formatar_numero(
                    item.get(
                        "consumido"
                    )
                )
            )


            print(
                "    Nível:",
                f'{item.get("nivel", 0)}%'
            )


            print(
                "    Status:",
                item.get(
                    "status",
                    "DESCONHECIDO"
                )
            )


    pausa()


# ============================================================
# ATUALIZAR DADOS
# ============================================================

async def atualizar_dados(
    device,
    sessao
):

    limpar_tela()

    titulo(
        "ATUALIZAR DADOS"
    )


    print(
        "Coletando informações atuais..."
    )

    print()


    try:

        await asyncio.wait_for(

            device.coletar(),

            timeout=15

        )


        sessao.ativar(
            device
        )


        print(
            "Dados atualizados com sucesso."
        )


    except asyncio.TimeoutError:

        print(
            "A impressora demorou para responder."
        )


    except Exception as erro:

        print(
            "Erro:",
            erro
        )


    pausa()


# ============================================================
# PÁGINA DE TESTE
# ============================================================

async def pagina_teste(
    device,
    sessao
):

    limpar_tela()

    titulo(
        "PÁGINA DE TESTE"
    )


    print(
        "Impressora:",
        device.modelo()
    )


    print(
        "IP:",
        device.ip
    )


    print()


    print(
        "Esta função será integrada ao módulo"
    )


    print(
        "de página de teste da impressora."
    )


    print()


    print(
        "Objetivo:"
    )


    print(
        "- imprimir padrão preto e branco"
    )


    print(
        "- avaliar unidade de imagem"
    )


    print(
        "- verificar manchas"
    )


    print(
        "- verificar linhas"
    )


    print(
        "- verificar falhas de impressão"
    )


    print()


    print(
        "MÓDULO PREPARADO PARA INTEGRAÇÃO."
    )


    pausa()


# ============================================================
# ETIQUETA DA IMPRESSORA
# ============================================================

async def etiqueta_impressora(
    device,
    sessao
):

    limpar_tela()

    titulo(
        "ETIQUETA DA IMPRESSORA"
    )


    print(
        "Aqui entra o módulo de impressão da"
    )


    print(
        "etiqueta TSC da impressora."
    )


    print()


    print(
        "Dados disponíveis:"
    )


    print(
        "Modelo:",
        device.modelo()
    )


    print(
        "Serial:",
        device.serial()
    )


    print(
        "Contador:",
        formatar_numero(
            device.contador()
        )
    )


    print()


    print(
        "MÓDULO DE ETIQUETA PRONTO PARA INTEGRAÇÃO."
    )


    pausa()


# ============================================================
# PRODUÇÃO
# ============================================================

def producao(
    device,
    sessao
):

    limpar_tela()

    titulo(
        "PRODUÇÃO"
    )


    print(
        "Futuro módulo de produção."
    )


    print()


    print(
        "Aqui vamos trabalhar com:"
    )


    print(
        "  - etiqueta de unidade"
    )


    print(
        "  - etiqueta de cartucho"
    )


    print(
        "  - número de série"
    )


    print(
        "  - part number"
    )


    print(
        "  - rastreabilidade"
    )


    print(
        "  - operador"
    )


    print(
        "  - data"
    )


    pausa()


# ============================================================
# RMA / GARANTIA
# ============================================================

def rma(
    device,
    sessao
):

    limpar_tela()

    titulo(
        "RMA / GARANTIA"
    )


    print(
        "Futuro módulo de RMA e garantia."
    )


    print()


    print(
        "A sessão atual já fornece:"
    )


    print(
        "  - modelo"
    )


    print(
        "  - serial"
    )


    print(
        "  - contador"
    )


    print(
        "  - IP"
    )


    print(
        "  - estado"
    )


    print(
        "  - suprimentos"
    )


    pausa()


# ============================================================
# MENU
# ============================================================

def menu():

    print()

    linha()

    print(
        "MENU PRINCIPAL"
    )

    linha()

    print()


    print(
        "[1] Diagnóstico"
    )


    print(
        "[2] Atualizar dados"
    )


    print(
        "[3] Página de teste"
    )


    print(
        "[4] Etiqueta da impressora"
    )


    print(
        "[5] Produção"
    )


    print(
        "[6] RMA / Garantia"
    )


    print(
        "[7] Trocar impressora"
    )


    print(
        "[0] Encerrar"
    )


    print()


    return input(
        "Escolha: "
    ).strip()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

async def executar():

    device = await descobrir_impressoras()


    if device is None:

        return


    sessao = ativar_sessao(
        device
    )


    while True:

        limpar_tela()

        titulo(
            "PRINTER ASSISTANT"
        )


        exibir_impressora(
            device,
            sessao
        )


        escolha = menu()


        if escolha == "1":

            await diagnostico(
                device,
                sessao
            )


        elif escolha == "2":

            await atualizar_dados(
                device,
                sessao
            )


        elif escolha == "3":

            await pagina_teste(
                device,
                sessao
            )


        elif escolha == "4":

            await etiqueta_impressora(
                device,
                sessao
            )


        elif escolha == "5":

            producao(
                device,
                sessao
            )


        elif escolha == "6":

            rma(
                device,
                sessao
            )


        elif escolha == "7":

            device = await descobrir_impressoras()


            if device is None:

                print()

                print(
                    "Nenhuma nova impressora selecionada."
                )

                pausa()

                continue


            sessao = ativar_sessao(
                device
            )


        elif escolha == "0":

            limpar_tela()

            titulo(
                "PRINTER ASSISTANT"
            )


            print(
                "Sessão encerrada."
            )


            print()

            break


        else:

            print()

            print(
                "Opção inválida."
            )


            pausa()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            executar()
        )


    except KeyboardInterrupt:

        print()

        print()

        print(
            "Programa encerrado pelo usuário."
        )