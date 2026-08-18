import asyncio
import json
import socket
import ipaddress
import subprocess
from pathlib import Path

from core.device import PrinterDevice


# ============================================================
# PRINTER ASSISTANT - SCANNER
# ============================================================
#
# Descoberta de equipamentos de impressão.
#
# FLUXO:
#
#   1. Descobre a rede local
#   2. Consulta tabela ARP
#   3. Se necessário, faz descoberta leve por PING
#   4. Testa RAW/9100 somente nos hosts conhecidos
#   5. Identifica os equipamentos em paralelo
#   6. Executa a coleta completa do PrinterDevice:
#
#          PJL
#           ↓
#        SYSDEBUG
#           ↓
#          SNMP
#           ↓
#   associação de seriais dos consumíveis
#
#   7. Mostra os equipamentos encontrados
#   8. Mostra identificação, contador e suprimentos
#   9. Permite selecionar uma impressora
#  10. Salva a descoberta em printers_found.json
#
# O IP existe internamente, mas não é a informação principal
# apresentada ao técnico.
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

PRINTERS_FOUND = BASE_DIR / "printers_found.json"


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PORTA_RAW = 9100

TIMEOUT_RAW = 0.8

# O PrinterDevice já possui seus próprios timeouts internos
# para PJL, SYSDEBUG e SNMP.
#
# Portanto NÃO colocamos um timeout curto em volta de
# device.coletar(), pois isso poderia cancelar o fluxo antes
# que SNMP terminasse.
#
TIMEOUT_COLETA = 75


# ============================================================
# REDE LOCAL
# ============================================================

def descobrir_rede():

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.connect(
            ("8.8.8.8", 80)
        )

        ip = sock.getsockname()[0]

        sock.close()

    except Exception:

        ip = socket.gethostbyname(
            socket.gethostname()
        )


    partes = ip.split(".")

    if len(partes) != 4:

        raise RuntimeError(
            "Não foi possível descobrir a rede local."
        )


    rede = (
        f"{partes[0]}."
        f"{partes[1]}."
        f"{partes[2]}.0/24"
    )


    return ip, rede


# ============================================================
# ARP
# ============================================================

def consultar_arp():

    encontrados = {}

    try:

        resultado = subprocess.run(

            ["arp", "-a"],

            capture_output=True,

            text=True,

            encoding="cp850",

            errors="ignore",

            timeout=5

        )

    except Exception:

        return encontrados


    for linha in resultado.stdout.splitlines():

        linha = linha.strip()


        # ----------------------------------------------------
        # Exemplo Windows:
        #
        # 192.168.14.134    00-11-22-33-44-55    dynamic
        # ----------------------------------------------------

        partes = linha.split()

        if len(partes) < 2:

            continue


        ip = partes[0]

        mac = partes[1]


        try:

            ipaddress.ip_address(ip)

        except ValueError:

            continue


        mac_normalizado = mac.lower()


        if mac_normalizado in (
            "ff-ff-ff-ff-ff-ff",
            "ff:ff:ff:ff:ff:ff"
        ):

            continue


        if mac_normalizado in (
            "00-00-00-00-00-00",
            "00:00:00:00:00:00"
        ):

            continue


        encontrados[ip] = mac


    return encontrados


# ============================================================
# PING
# ============================================================

async def ping_host(ip):

    try:

        processo = await asyncio.create_subprocess_exec(

            "ping",
            "-n",
            "1",
            "-w",
            "250",
            str(ip),

            stdout=asyncio.subprocess.DEVNULL,

            stderr=asyncio.subprocess.DEVNULL

        )


        codigo = await asyncio.wait_for(

            processo.wait(),

            timeout=0.5

        )


        if codigo == 0:

            return str(ip)


    except Exception:

        pass


    return None


# ============================================================
# ATUALIZAR ARP
# ============================================================

async def atualizar_descoberta_local(
    rede
):

    rede_obj = ipaddress.ip_network(
        rede
    )


    tarefas = [

        ping_host(ip)

        for ip in rede_obj.hosts()

    ]


    resultados = await asyncio.gather(
        *tarefas
    )


    encontrados = []


    for ip in resultados:

        if ip:

            encontrados.append(ip)


    return encontrados


# ============================================================
# TESTAR RAW
# ============================================================

async def testar_raw(ip):

    try:

        leitor, escritor = await asyncio.wait_for(

            asyncio.open_connection(

                ip,

                PORTA_RAW

            ),

            timeout=TIMEOUT_RAW

        )


        escritor.close()

        try:

            await escritor.wait_closed()

        except Exception:

            pass


        return True


    except Exception:

        return False


# ============================================================
# IDENTIFICAÇÃO / COLETA COMPLETA
# ============================================================

async def identificar(ip):

    device = PrinterDevice(
        ip=ip
    )


    try:

        # ----------------------------------------------------
        # IMPORTANTE
        #
        # Antes o scanner chamava somente:
        #
        #     device.coletar_pjl()
        #
        # Isso identificava a impressora, mas NÃO executava
        # SYSDEBUG, SNMP e associação dos seriais.
        #
        # Agora usamos o fluxo oficial do PrinterDevice:
        #
        #     device.coletar()
        #
        # que executa:
        #
        #     PJL
        #     SYSDEBUG
        #     SNMP
        #     associação dos seriais dos consumíveis
        #
        # ----------------------------------------------------

        await asyncio.wait_for(

            device.coletar(),

            timeout=TIMEOUT_COLETA

        )


        return {

            "device": device,

            "timeout": False,

            "erro": None

        }


    except asyncio.TimeoutError:

        return {

            "device": device,

            "timeout": True,

            "erro":
                "Coleta completa excedeu o tempo limite."

        }


    except Exception as erro:

        return {

            "device": device,

            "timeout": False,

            "erro": str(erro)

        }


# ============================================================
# DESCOBRIR CANDIDATOS
# ============================================================

async def descobrir_candidatos():

    ip_local, rede = descobrir_rede()


    print()

    print(
        "IP deste computador:",
        ip_local
    )

    print(
        "Rede local:",
        rede
    )


    # ========================================================
    # ARP
    # ========================================================

    print()

    print(
        "Consultando tabela ARP..."
    )


    arp = consultar_arp()


    # --------------------------------------------------------
    # Se a tabela ARP estiver muito pequena, fazemos um
    # preenchimento leve através de ping.
    #
    # Isso NÃO significa escanear SNMP/WEB/etc.
    #
    # É somente descoberta de hosts ativos.
    # --------------------------------------------------------

    if len(arp) < 2:

        print(
            "Poucos dispositivos encontrados pela ARP."
        )

        print(
            "Atualizando descoberta local..."
        )


        hosts_ativos = await atualizar_descoberta_local(
            rede
        )


        for ip in hosts_ativos:

            arp.setdefault(
                ip,
                "desconhecido"
            )


    # --------------------------------------------------------
    # Remove o próprio computador.
    # --------------------------------------------------------

    arp.pop(
        ip_local,
        None
    )


    print()

    print(
        f"{len(arp)} dispositivos conhecidos."
    )


    # ========================================================
    # TESTAR 9100
    # ========================================================

    print()

    print(
        "Testando porta RAW 9100..."
    )


    ips = list(
        arp.keys()
    )


    tarefas = [

        testar_raw(ip)

        for ip in ips

    ]


    resultados_raw = await asyncio.gather(
        *tarefas
    )


    candidatos = []


    for ip, ativo in zip(
        ips,
        resultados_raw
    ):

        if ativo:

            candidatos.append(ip)


    return (
        ip_local,
        rede,
        candidatos
    )


# ============================================================
# NOME DO EQUIPAMENTO
# ============================================================

def nome_equipamento(device):

    identificacao = (
        device.identificacao
    )


    fabricante = identificacao.get(
        "fabricante",
        "Desconhecido"
    )


    modelo = identificacao.get(
        "modelo",
        "Desconhecido"
    )


    if modelo != "Desconhecido":

        return modelo


    if fabricante != "Desconhecido":

        return fabricante


    return (
        "Equipamento de impressão "
        "não identificado"
    )


# ============================================================
# FORMATAR NÚMERO
# ============================================================

def formatar_numero(
    valor
):

    if valor is None:

        return "desconhecido"


    try:

        return f"{int(valor):,}".replace(
            ",",
            "."
        )

    except (
        ValueError,
        TypeError
    ):

        return str(
            valor
        )


# ============================================================
# EXIBIR SUPRIMENTOS
# ============================================================

def exibir_suprimentos(
    device
):

    supplies = device.supplies


    if not supplies:

        print(
            "    Suprimentos: nenhum dado disponível."
        )

        return


    print()

    print(
        "    SUPRIMENTOS:"
    )


    for numero, supply in enumerate(
        supplies,
        start=1
    ):

        if not isinstance(
            supply,
            dict
        ):

            print(
                f"        [{numero}] {supply}"
            )

            continue


        tipo = (
            supply.get(
                "tipo"
            )

            or
            ""
        )


        nome = (

            supply.get(
                "nome"
            )

            or

            supply.get(
                "name"
            )

            or

            supply.get(
                "descricao"
            )

            or

            supply.get(
                "description"
            )

            or

            tipo

            or

            "Consumível"

        )


        nivel = (

            supply.get(
                "nivel"
            )

            if supply.get(
                "nivel"
            ) is not None

            else

            supply.get(
                "level"
            )
        )


        capacidade = (

            supply.get(
                "capacidade"
            )

            if supply.get(
                "capacidade"
            ) is not None

            else

            supply.get(
                "maximo"
            )
        )


        serial = (

            supply.get(
                "numero_serie"
            )

            or

            supply.get(
                "serial"
            )

            or

            "não informado"
        )


        part_number = (

            supply.get(
                "part_number"
            )

            or

            supply.get(
                "partnumber"
            )

            or

            supply.get(
                "part"
            )

            or

            "não informado"
        )


        print()

        print(
            f"        [{numero}] {nome}"
        )


        if tipo:

            print(
                "            Tipo:",
                tipo
            )


        print(
            "            Nível:",
            (
                formatar_numero(
                    nivel
                )
                if nivel is not None
                else "não informado"
            )
        )


        if capacidade is not None:

            print(
                "            Capacidade:",
                formatar_numero(
                    capacidade
                )
            )


        print(
            "            Part Number:",
            part_number
        )


        print(
            "            Serial:",
            serial
        )


# ============================================================
# EXIBIR LISTA
# ============================================================

def exibir_lista(
    resultados
):

    print()

    print("=" * 70)

    print(
        "IMPRESSORAS ENCONTRADAS"
    )

    print("=" * 70)


    if not resultados:

        print()

        print(
            "Nenhuma impressora foi identificada."
        )

        return


    for numero, item in enumerate(
        resultados,
        start=1
    ):

        device = item["device"]

        identificacao = (
            device.identificacao
        )


        print()

        print(
            f"[{numero}]",
            nome_equipamento(
                device
            )
        )


        fabricante = identificacao.get(
            "fabricante",
            "Desconhecido"
        )


        modelo = identificacao.get(
            "modelo",
            "Desconhecido"
        )


        serial = identificacao.get(
            "serial",
            "Desconhecido"
        )


        contador = identificacao.get(
            "contador"
        )


        print(
            "    Fabricante:",
            fabricante
        )


        print(
            "    Modelo:",
            modelo
        )


        print(
            "    Serial:",
            serial
        )


        print(
            "    Contador:",
            formatar_numero(
                contador
            )
        )


        print(
            "    Estado:",
            device.estado()
        )


        print(
            "    Suprimentos:",
            device.total_supplies()
        )


        # ----------------------------------------------------
        # Mostrar suprimentos somente quando existirem.
        # ----------------------------------------------------

        exibir_suprimentos(
            device
        )


        # ----------------------------------------------------
        # IP continua disponível, mas secundário.
        # ----------------------------------------------------

        print()

        print(
            "    [rede:",
            device.ip,
            "]"
        )


        if item.get(
            "timeout"
        ):

            print()

            print(
                "    AVISO: coleta do equipamento "
                "excedeu o tempo limite."
            )


        if item.get(
            "erro"
        ):

            print()

            print(
                "    AVISO:",
                item["erro"]
            )


# ============================================================
# SELECIONAR
# ============================================================

def selecionar(
    resultados
):

    if not resultados:

        return None


    print()

    print("=" * 70)

    print(
        "SELECIONE A IMPRESSORA"
    )

    print("=" * 70)


    print()

    escolha = input(
        "Digite o número do equipamento "
        "(ou ENTER para cancelar): "
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
            "Seleção inválida."
        )

        return None


    if (
        numero < 1
        or
        numero > len(
            resultados
        )
    ):

        print()

        print(
            "Número fora da lista."
        )

        return None


    return resultados[
        numero - 1
    ]["device"]


# ============================================================
# SALVAR DESCOBERTA
# ============================================================

def salvar_resultados(
    rede,
    resultados
):

    dados = []


    for item in resultados:

        device = item["device"]


        registro = device.to_dict()


        registro[
            "scanner"
        ] = {

            "timeout_coleta":
                bool(
                    item.get(
                        "timeout"
                    )
                ),

            "erro_coleta":
                item.get(
                    "erro"
                )

        }


        dados.append(
            registro
        )


    with open(

        PRINTERS_FOUND,

        "w",

        encoding="utf-8"

    ) as arquivo:

        json.dump(

            {

                "rede":
                    rede,

                "quantidade":
                    len(dados),

                "equipamentos":
                    dados

            },

            arquivo,

            indent=4,

            ensure_ascii=False

        )


# ============================================================
# EXIBIR EQUIPAMENTO SELECIONADO
# ============================================================

def exibir_equipamento_selecionado(
    device
):

    print()

    print("=" * 70)

    print(
        "EQUIPAMENTO SELECIONADO"
    )

    print("=" * 70)


    print()

    identificacao = (
        device.identificacao
    )


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


    contador = identificacao.get(
        "contador"
    )


    print(
        "Contador:",
        formatar_numero(
            contador
        )
    )


    print()

    print(
        "Estado:",
        device.estado()
    )


    print(
        "Suprimentos:",
        device.total_supplies()
    )


    exibir_suprimentos(
        device
    )


    print()

    print(
        "IP interno:",
        device.ip
    )


    print()

    print(
        "IMPRESSORA PRONTA PARA O PRÓXIMO MÓDULO."
    )


    print()


# ============================================================
# MAIN
# ============================================================

async def main():

    print()

    print("=" * 70)

    print(
        "PRINTER ASSISTANT - "
        "DESCOBERTA DE IMPRESSORAS"
    )

    print("=" * 70)


    print()

    print(
        "Descobrindo equipamentos de impressão..."
    )


    try:

        (
            ip_local,
            rede,
            candidatos

        ) = await descobrir_candidatos()


    except Exception as erro:

        print()

        print(
            "ERRO durante descoberta:",
            erro
        )

        return


    print()

    print("=" * 70)

    print(
        "DISPOSITIVOS COM RAW/9100"
    )

    print("=" * 70)


    if not candidatos:

        print()

        print(
            "Nenhum equipamento encontrado."
        )

        return


    print()


    for numero, ip in enumerate(
        candidatos,
        start=1
    ):

        print(
            f"[{numero}] equipamento de impressão "
            f"detectado em {ip}"
        )


    # ========================================================
    # COLETA COMPLETA PARALELA
    # ========================================================

    print()

    print(
        "Identificando e coletando dados "
        "dos equipamentos..."
    )

    print()

    print(
        "PJL + SYSDEBUG + SNMP + "
        "seriais dos consumíveis"
    )


    tarefas = [

        identificar(ip)

        for ip in candidatos

    ]


    identificados = await asyncio.gather(
        *tarefas
    )


    resultados = list(
        identificados
    )


    # ========================================================
    # ORDENAR
    # ========================================================
    #
    # Equipamentos com modelo conhecido ficam primeiro.
    # Depois, equipamentos com serial conhecido.
    #

    resultados.sort(

        key=lambda item: (

            item["device"].modelo()
            == "Desconhecido",

            item["device"].serial()
            == "Desconhecido"

        )

    )


    # ========================================================
    # SALVAR
    # ========================================================

    salvar_resultados(
        rede,
        resultados
    )


    # ========================================================
    # EXIBIR
    # ========================================================

    exibir_lista(
        resultados
    )


    # ========================================================
    # SELEÇÃO
    # ========================================================

    device = selecionar(
        resultados
    )


    if device is None:

        print()

        print(
            "Nenhum equipamento selecionado."
        )

        return


    # ========================================================
    # RESULTADO
    # ========================================================

    exibir_equipamento_selecionado(
        device
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )