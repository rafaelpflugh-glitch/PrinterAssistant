import asyncio
import json
from pathlib import Path
from datetime import datetime

from core.device import PrinterDevice
from core.asset import salvar_ativo


# ============================================================
# PRINTER ASSISTANT - COLETOR CENTRAL
# ============================================================
#
# O collector NÃO conversa mais diretamente com PJL/SNMP.
#
# Arquitetura:
#
# collector.py
#       |
#       v
# PrinterDevice
#       |
#       +----> PJL
#       |
#       +----> SNMP
#       |
#       v
# snapshot + ativo
#
# Isso evita que cada módulo do programa tenha que saber
# como uma impressora é coletada.
#
# ============================================================


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


PRINTER_DATA = (
    BASE_DIR /
    "printer_data.json"
)


# ============================================================
# UTILIDADES
# ============================================================

def formatar_numero(valor):

    if valor is None:
        return "Desconhecido"

    try:

        return f"{int(valor):,}".replace(
            ",",
            "."
        )

    except:

        return str(valor)


# ============================================================
# ENTRADA
# ============================================================

def solicitar_ip():

    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()


    if not ip:

        raise ValueError(
            "IP não informado."
        )


    return ip


# ============================================================
# SALVAR SNAPSHOT
# ============================================================

def salvar_snapshot(
    device
):

    dados = {

        "data":
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "ip":
            device.ip,

        "identificacao":
            device.identificacao,

        "conectividade":
            device.conectividade,

        "supplies":
            device.supplies,

        "estado":
            device.estado(),

        "total_supplies":
            device.total_supplies()

    }


    with open(

        PRINTER_DATA,

        "w",

        encoding="utf-8"

    ) as arquivo:

        json.dump(

            dados,

            arquivo,

            indent=4,

            ensure_ascii=False

        )


    return dados


# ============================================================
# EXIBIR RESUMO
# ============================================================

def exibir_resumo(
    device
):

    identificacao = (
        device.identificacao
    )


    conectividade = (
        device.conectividade
    )


    supplies = (
        device.supplies
    )


    print()

    print("=" * 60)

    print(
        "RESUMO DA IMPRESSORA"
    )

    print("=" * 60)


    print()

    print(
        "IP:",
        device.ip
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
        "PJL:",
        "ATIVO"
        if conectividade.get(
            "pjl"
        )
        else
        "INATIVO"
    )


    print(
        "SNMP:",
        "ATIVO"
        if conectividade.get(
            "snmp"
        )
        else
        "INATIVO"
    )


    print(
        "Estado:",
        device.estado()
    )


    print(
        "Suprimentos:",
        device.total_supplies()
    )


    # ========================================================
    # SUPRIMENTOS
    # ========================================================

    print()

    print("=" * 60)

    print(
        "SUPRIMENTOS"
    )

    print("=" * 60)


    if not supplies:

        print()

        print(
            "Nenhum suprimento encontrado."
        )


        return


    for numero, supply in enumerate(

        supplies,

        start=1

    ):

        print()

        print(
            f"[{numero}]",
            supply.get(
                "nome",
                "Desconhecido"
            )
        )


        print(
            "    Capacidade:",
            formatar_numero(
                supply.get(
                    "capacidade"
                )
            )
        )


        print(
            "    Restante:",
            formatar_numero(
                supply.get(
                    "restante"
                )
            )
        )


        print(
            "    Consumido:",
            formatar_numero(
                supply.get(
                    "consumido"
                )
            )
        )


        print(
            "    Nível:",
            f'{supply.get("nivel", 0)}%'
        )


        print(
            "    Status:",
            supply.get(
                "status",
                "DESCONHECIDO"
            )
        )


# ============================================================
# SALVAR ATIVO
# ============================================================

def atualizar_ativo(
    device
):

    identificacao = (
        device.identificacao
    )


    serial = (
        identificacao.get(
            "serial"
        )
    )


    if serial in (

        None,

        "",

        "Desconhecido"

    ):

        print()

        print(
            "Ativo não atualizado:"
        )

        print(
            "número de série não encontrado."
        )

        return False


    try:

        salvar_ativo(

            identificacao,

            device.conectividade,

            device.supplies

        )


        return True


    except Exception as erro:

        print()

        print(
            "Aviso ao atualizar ativo:",
            erro
        )


        return False


# ============================================================
# MAIN
# ============================================================

async def main():

    print()

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - COLETOR"
    )

    print("=" * 60)


    # ========================================================
    # IP
    # ========================================================

    ip = solicitar_ip()


    print()

    print("=" * 60)

    print(
        "COLETA DA IMPRESSORA"
    )

    print("=" * 60)


    print()

    print(
        "IP:",
        ip
    )


    # ========================================================
    # DEVICE
    # ========================================================

    print()

    print(
        "Criando dispositivo..."
    )


    device = PrinterDevice(
        ip
    )


    print()

    print(
        "Coletando dados..."
    )


    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # PrinterDevice.coletar()
    # é async.
    #
    # Portanto:
    #
    # await device.coletar()
    #
    # --------------------------------------------------------

    try:

        await device.coletar()


    except Exception as erro:

        print()

        print(
            "ERRO durante a coleta:"
        )

        print(
            erro
        )

        print()

        print(
            "A coleta foi interrompida."
        )

        return


    # ========================================================
    # SNAPSHOT
    # ========================================================

    salvar_snapshot(
        device
    )


    # ========================================================
    # ATIVO
    # ========================================================

    ativo_salvo = (
        atualizar_ativo(
            device
        )
    )


    # ========================================================
    # RESUMO
    # ========================================================

    exibir_resumo(
        device
    )


    # ========================================================
    # FINAL
    # ========================================================

    print()

    print("=" * 60)

    print(
        "COLETA CONCLUÍDA"
    )

    print("=" * 60)


    print()

    print(
        "Snapshot salvo em:"
    )


    print(
        PRINTER_DATA
    )


    if ativo_salvo:

        print()

        print(
            "Ativo atualizado com sucesso."
        )


    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )