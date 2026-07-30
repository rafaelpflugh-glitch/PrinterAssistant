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
# Fluxo:
#
#   1. Descobre a rede local
#   2. Consulta tabela ARP
#   3. Testa RAW/9100 somente nos IPs conhecidos
#   4. Identifica os candidatos em paralelo
#   5. Mostra uma lista amigável ao técnico
#   6. Técnico seleciona pelo equipamento
#
# O IP continua existindo internamente, mas não é
# a informação principal para o técnico.
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

PRINTERS_FOUND = BASE_DIR / "printers_found.json"


PORTA_RAW = 9100

TIMEOUT_RAW = 0.8

TIMEOUT_IDENTIFICACAO = 8


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


        # Exemplo Windows:
        #
        # 192.168.14.134    00-11-22-33-44-55    dynamic
        #

        partes = linha.split()

        if len(partes) < 2:

            continue


        ip = partes[0]

        mac = partes[1]


        try:

            ipaddress.ip_address(ip)

        except ValueError:

            continue


        if mac.lower() in (
            "ff-ff-ff-ff-ff-ff",
            "ff:ff:ff:ff:ff:ff"
        ):

            continue


        if mac.lower() in (
            "00-00-00-00-00-00",
            "00:00:00:00:00:00"
        ):

            continue


        encontrados[ip] = mac


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
# IDENTIFICAÇÃO RÁPIDA
# ============================================================

async def identificar(ip):

    device = PrinterDevice(
        ip=ip
    )


    try:

        # ----------------------------------------------------
        # A identificação PJL atual é síncrona.
        #
        # Não podemos simplesmente executar isso diretamente
        # dentro do event loop porque um equipamento lento
        # travaria todo o scanner.
        #
        # Por isso ela roda em uma thread.
        # ----------------------------------------------------

        await asyncio.wait_for(

            asyncio.to_thread(
                device.coletar_pjl
            ),

            timeout=TIMEOUT_IDENTIFICACAO

        )

    except asyncio.TimeoutError:

        return {
            "device": device,
            "timeout": True
        }

    except Exception:

        return {
            "device": device,
            "timeout": False
        }


    return {
        "device": device,
        "timeout": False
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


    print()

    print(
        "Consultando tabela ARP..."
    )


    arp = consultar_arp()


    # --------------------------------------------------------
    # Se a tabela ARP estiver muito pequena, fazemos um
    # preenchimento leve através de ping.
    #
    # Isso não significa escanear SNMP/WEB/etc.
    # É somente descoberta de hosts ativos.
    # --------------------------------------------------------

    if len(arp) < 2:

        print(
            "Poucos dispositivos encontrados pela ARP."
        )

        print(
            "Atualizando descoberta local..."
        )


        rede_obj = ipaddress.ip_network(
            rede
        )


        async def ping(ip):

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


                return (
                    str(ip)
                    if codigo == 0
                    else None
                )


            except Exception:

                return None


        tarefas = [

            ping(ip)

            for ip in rede_obj.hosts()

        ]


        resultados = await asyncio.gather(
            *tarefas
        )


        for ip in resultados:

            if ip:

                arp.setdefault(
                    ip,
                    "desconhecido"
                )


    # --------------------------------------------------------
    # Remove o próprio computador
    # --------------------------------------------------------

    arp.pop(
        ip_local,
        None
    )


    print()

    print(
        f"{len(arp)} dispositivos conhecidos pela tabela ARP."
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


    resultados = await asyncio.gather(
        *tarefas
    )


    candidatos = []


    for ip, ativo in zip(
        ips,
        resultados
    ):

        if ativo:

            candidatos.append(ip)


    return (
        ip_local,
        rede,
        candidatos
    )


# ============================================================
# EXIBIR EQUIPAMENTO
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
# EXIBIR LISTA
# ============================================================

def exibir_lista(resultados):

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


        serial = identificacao.get(
            "serial",
            "Desconhecido"
        )


        contador = identificacao.get(
            "contador"
        )


        if contador is None:

            contador_texto = (
                "desconhecido"
            )

        else:

            contador_texto = (
                f"{contador:,}".replace(
                    ",",
                    "."
                )
            )


        print(
            "    Fabricante:",
            fabricante
        )


        print(
            "    Serial:",
            serial
        )


        print(
            "    Contador:",
            contador_texto
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
        # IP fica disponível, mas secundário.
        # ----------------------------------------------------

        print(
            "    [rede:",
            device.ip + "]"
        )


        if item.get("timeout"):

            print(
                "    Aviso: equipamento respondeu lentamente."
            )


# ============================================================
# SELECIONAR
# ============================================================

def selecionar(resultados):

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


    if numero < 1 or numero > len(
        resultados
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

            "timeout_identificacao":
                bool(
                    item.get(
                        "timeout"
                    )
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

                "rede": rede,

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
# MAIN
# ============================================================

async def main():

    print()

    print("=" * 70)

    print(
        "PRINTER ASSISTANT - DESCOBERTA DE IMPRESSORAS"
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
            f"detectado"
        )


    # ========================================================
    # IDENTIFICAÇÃO PARALELA
    # ========================================================

    print()

    print(
        "Identificando equipamentos..."
    )


    tarefas = [

        identificar(ip)

        for ip in candidatos

    ]


    identificados = await asyncio.gather(
        *tarefas
    )


    resultados = []


    for item in identificados:

        resultados.append(
            item
        )


    # ========================================================
    # ORDENAR
    # ========================================================

    # Equipamentos identificados ficam primeiro.

    resultados.sort(

        key=lambda item: (

            item["device"].modelo()
            == "Desconhecido",

            item["device"].serial()
            == "Desconhecido"

        )

    )


    salvar_resultados(
        rede,
        resultados
    )


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
        identificacao["fabricante"]
    )


    print(
        "Modelo:",
        identificacao["modelo"]
    )


    print(
        "Família:",
        identificacao["familia"]
    )


    print(
        "Tipo:",
        identificacao["tipo"]
    )


    print(
        "Serial:",
        identificacao["serial"]
    )


    contador = identificacao[
        "contador"
    ]


    if contador is None:

        print(
            "Contador: desconhecido"
        )

    else:

        print(
            "Contador:",
            f"{contador:,}".replace(
                ",",
                "."
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
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )