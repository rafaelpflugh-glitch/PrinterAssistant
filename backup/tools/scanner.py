
import asyncio
import json
import socket
import subprocess
import platform
from pathlib import Path

from core.device import PrinterDevice


# ============================================================
# PRINTER ASSISTANT - SCANNER
# ============================================================
#
# Descoberta de impressoras na rede.
#
# ARQUITETURA:
#
#   1. Descobre a rede local
#   2. Descobre hosts ativos por ping
#   3. Testa RAW/9100
#   4. Identifica candidatos via PJL
#   5. Somente candidatos identificados recebem SNMP
#   6. SNMP roda de forma controlada
#   7. Salva somente resultados relevantes
#
# IMPORTANTE:
#
# NÃO fazemos:
#
#   todos os hosts -> PJL + SNMP simultaneamente
#
# Isso sobrecarrega a rede e provoca falsos timeouts.
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

PRINTERS_FOUND = BASE_DIR / "printers_found.json"


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PORTA_RAW = 9100

TIMEOUT_PING = 0.4

TIMEOUT_RAW = 0.5

TIMEOUT_PJL = 8

TIMEOUT_SNMP = 12

MAX_IDENTIFICACAO = 4

MAX_SNMP = 2


# ============================================================
# DESCOBRIR IP / REDE
# ============================================================

def descobrir_rede():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    try:

        sock.connect(
            ("8.8.8.8", 80)
        )

        ip = sock.getsockname()[0]

    finally:

        sock.close()


    partes = ip.split(".")

    if len(partes) != 4:

        raise RuntimeError(
            "Não foi possível determinar o endereço IPv4."
        )


    rede = (
        f"{partes[0]}."
        f"{partes[1]}."
        f"{partes[2]}.0/24"
    )


    return ip, rede


# ============================================================
# PING
# ============================================================

def ping(ip):

    sistema = platform.system().lower()


    if sistema == "windows":

        comando = [

            "ping",
            "-n",
            "1",
            "-w",
            str(
                int(
                    TIMEOUT_PING * 1000
                )
            ),
            ip

        ]

    else:

        comando = [

            "ping",
            "-c",
            "1",
            "-W",
            "1",
            ip

        ]


    try:

        resultado = subprocess.run(

            comando,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL,

            timeout=2

        )

        return (
            resultado.returncode == 0
        )

    except Exception:

        return False


# ============================================================
# DESCOBERTA DE HOSTS
# ============================================================

def descobrir_hosts_ativos(rede):

    partes = rede.split(".")

    base = (
        f"{partes[0]}."
        f"{partes[1]}."
        f"{partes[2]}"
    )


    ips = [

        f"{base}.{numero}"

        for numero in range(
            1,
            255
        )

    ]


    ativos = []


    # --------------------------------------------------------
    # ThreadPool para ping.
    #
    # Não usamos asyncio subprocess para isso porque o ping
    # do Windows pode gerar bastante ruído no event loop.
    # --------------------------------------------------------

    from concurrent.futures import ThreadPoolExecutor


    with ThreadPoolExecutor(
        max_workers=64
    ) as executor:

        resultados = executor.map(
            ping,
            ips
        )


        for ip, ativo in zip(
            ips,
            resultados
        ):

            if ativo:

                ativos.append(
                    ip
                )


    return ativos


# ============================================================
# RAW 9100
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
# TESTAR RAW EM PARALELO
# ============================================================

async def filtrar_raw(ips):

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

            candidatos.append(
                ip
            )


    return candidatos


# ============================================================
# IDENTIFICAÇÃO PJL
# ============================================================

async def identificar_pjl(ip):

    device = PrinterDevice(
        ip=ip
    )


    try:

        await asyncio.wait_for(

            asyncio.to_thread(
                device.coletar_pjl
            ),

            timeout=TIMEOUT_PJL

        )


    except asyncio.TimeoutError:

        print(
            f"[SCANNER] PJL timeout: {ip}"
        )

        return {

            "device": device,

            "pjl": False,

            "timeout": True

        }


    except Exception as erro:

        print(
            f"[SCANNER] Erro PJL {ip}: {erro}"
        )

        return {

            "device": device,

            "pjl": False,

            "timeout": False

        }


    # --------------------------------------------------------
    # Verificamos se realmente houve identificação.
    # --------------------------------------------------------

    identificacao = (
        device.identificacao
    )


    modelo = identificacao.get(
        "modelo"
    )


    serial = identificacao.get(
        "serial"
    )


    respondeu = (

        device.conectividade.get(
            "pjl",
            False
        )

        and

        (
            modelo != "Desconhecido"

            or

            serial != "Desconhecido"
        )

    )


    return {

        "device": device,

        "pjl": respondeu,

        "timeout": False

    }


# ============================================================
# IDENTIFICAÇÃO CONTROLADA
# ============================================================

async def identificar_candidatos(
    candidatos
):

    semaforo = asyncio.Semaphore(
        MAX_IDENTIFICACAO
    )


    async def executar(ip):

        async with semaforo:

            return await identificar_pjl(
                ip
            )


    tarefas = [

        executar(ip)

        for ip in candidatos

    ]


    return await asyncio.gather(
        *tarefas
    )


# ============================================================
# SNMP CONTROLADO
# ============================================================

async def atualizar_snmp(
    resultado
):

    device = resultado["device"]


    try:

        # ----------------------------------------------------
        # NÃO chamamos device.coletar().
        #
        # Isso é fundamental.
        #
        # PJL já foi coletado.
        #
        # Agora queremos SOMENTE SNMP.
        # ----------------------------------------------------

        await asyncio.wait_for(

            device.coletar_snmp(),

            timeout=TIMEOUT_SNMP

        )


    except asyncio.TimeoutError:

        print(
            f"[SCANNER] SNMP timeout: {device.ip}"
        )


    except Exception as erro:

        print(
            f"[SCANNER] Erro SNMP "
            f"{device.ip}: {erro}"
        )


    return resultado


# ============================================================
# SNMP CONTROLADO
# ============================================================

async def atualizar_snmp_lista(
    resultados
):

    semaforo = asyncio.Semaphore(
        MAX_SNMP
    )


    async def executar(item):

        async with semaforo:

            return await atualizar_snmp(
                item
            )


    tarefas = [

        executar(item)

        for item in resultados

    ]


    return await asyncio.gather(
        *tarefas
    )


# ============================================================
# NOME DO EQUIPAMENTO
# ============================================================

def nome_equipamento(
    device
):

    identificacao = (
        device.identificacao
    )


    modelo = identificacao.get(
        "modelo",
        "Desconhecido"
    )


    fabricante = identificacao.get(
        "fabricante",
        "Desconhecido"
    )


    if modelo != "Desconhecido":

        return modelo


    if fabricante != "Desconhecido":

        return fabricante


    return (
        "Equipamento não identificado"
    )


# ============================================================
# SALVAR
# ============================================================

def salvar_resultados(
    rede,
    resultados
):

    dados = []


    for item in resultados:

        device = item["device"]


        registro = device.to_dict()


        registro["scanner"] = {

            "pjl": bool(
                item.get(
                    "pjl"
                )
            ),

            "timeout": bool(
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
# EXIBIR RESULTADOS
# ============================================================

def exibir_resultados(
    resultados
):

    print()

    print(
        "=" * 70
    )

    print(
        "IMPRESSORAS ENCONTRADAS"
    )

    print(
        "=" * 70
    )


    if not resultados:

        print()

        print(
            "Nenhuma impressora identificada."
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


        print(
            "    Fabricante:",
            identificacao.get(
                "fabricante",
                "Desconhecido"
            )
        )


        print(
            "    Modelo:",
            identificacao.get(
                "modelo",
                "Desconhecido"
            )
        )


        print(
            "    Serial:",
            identificacao.get(
                "serial",
                "Desconhecido"
            )
        )


        contador = identificacao.get(
            "contador"
        )


        if contador is None:

            print(
                "    Contador: desconhecido"
            )

        else:

            print(
                "    Contador:",
                f"{contador:,}".replace(
                    ",",
                    "."
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


        print(
            "    [rede:",
            device.ip,
            "]"
        )


        print(
            "    PJL:",
            "ATIVO"
            if device.conectividade.get(
                "pjl"
            )
            else
            "INATIVO"
        )


        print(
            "    SNMP:",
            "ATIVO"
            if device.conectividade.get(
                "snmp"
            )
            else
            "INATIVO"
        )


        if item.get("timeout"):

            print(
                "    Aviso: PJL excedeu "
                f"{TIMEOUT_PJL}s."
            )


# ============================================================
# SELEÇÃO
# ============================================================

def selecionar(
    resultados
):

    if not resultados:

        return None


    print()

    print(
        "=" * 70
    )

    print(
        "SELECIONE A IMPRESSORA"
    )

    print(
        "=" * 70
    )


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
        numero > len(resultados)
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
# MAIN
# ============================================================

async def main():

    print()

    print(
        "=" * 70
    )

    print(
        "PRINTER ASSISTANT - "
        "DESCOBERTA DE IMPRESSORAS"
    )

    print(
        "=" * 70
    )


    print()

    print(
        "Descobrindo equipamentos..."
    )


    try:

        ip_local, rede = (
            descobrir_rede()
        )

    except Exception as erro:

        print()

        print(
            "Erro ao descobrir rede:",
            erro
        )

        return


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
    # HOSTS ATIVOS
    # ========================================================

    print()

    print(
        "Consultando dispositivos ativos..."
    )


    ativos = await asyncio.to_thread(

        descobrir_hosts_ativos,

        rede

    )


    ativos = [

        ip

        for ip in ativos

        if ip != ip_local

    ]


    print()

    print(
        f"{len(ativos)} dispositivos ativos encontrados."
    )


    if not ativos:

        print()

        print(
            "Nenhum dispositivo ativo encontrado."
        )

        return


    # ========================================================
    # RAW
    # ========================================================

    print()

    print(
        "Filtrando candidatos pela porta RAW 9100..."
    )


    candidatos = await filtrar_raw(
        ativos
    )


    print()

    print(
        f"{len(candidatos)} candidatos responderam "
        "em RAW/9100."
    )


    if not candidatos:

        print()

        print(
            "Nenhum equipamento respondeu "
            "na porta RAW 9100."
        )

        return


    # ========================================================
    # PJL
    # ========================================================

    print()

    print(
        "Identificando candidatos via PJL..."
    )


    resultados = await identificar_candidatos(
        candidatos
    )


    # --------------------------------------------------------
    # SOMENTE PJL REALMENTE IDENTIFICADO
    # --------------------------------------------------------

    identificados = [

        item

        for item in resultados

        if item.get("pjl")

    ]


    if not identificados:

        print()

        print(
            "Nenhum candidato foi identificado via PJL."
        )

        return


    print()

    print(
        f"{len(identificados)} equipamento(s) "
        "identificado(s) via PJL."
    )


    # ========================================================
    # SNMP
    # ========================================================

    print()

    print(
        "Consultando SNMP somente "
        "nos equipamentos identificados..."
    )


    identificados = await atualizar_snmp_lista(
        identificados
    )


    # ========================================================
    # ORDENAR
    # ========================================================

    identificados.sort(

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

        identificados

    )


    print()

    print(
        "[SCANNER] Resultado salvo em:"
    )

    print(
        PRINTERS_FOUND
    )


    # ========================================================
    # EXIBIR
    # ========================================================

    exibir_resultados(
        identificados
    )


    # ========================================================
    # SELEÇÃO
    # ========================================================

    device = selecionar(
        identificados
    )


    if device is None:

        print()

        print(
            "Nenhum equipamento selecionado."
        )

        return


    # ========================================================
    # EQUIPAMENTO SELECIONADO
    # ========================================================

    identificacao = (
        device.identificacao
    )


    print()

    print(
        "=" * 70
    )

    print(
        "EQUIPAMENTO SELECIONADO"
    )

    print(
        "=" * 70
    )


    print()

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


    print(
        "PJL:",
        "ATIVO"
        if device.conectividade["pjl"]
        else
        "INATIVO"
    )


    print(
        "SNMP:",
        "ATIVO"
        if device.conectividade["snmp"]
        else
        "INATIVO"
    )


    print()

    print(
        "IP interno:",
        device.ip
    )


    print()

    print(
        "=" * 70
    )

    print(
        "IMPRESSORA PRONTA PARA "
        "O PRÓXIMO MÓDULO."
    )

    print(
        "=" * 70
    )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print()

        print(
            "Programa encerrado pelo usuário."
        )

