import asyncio
import json
from pathlib import Path
from datetime import datetime

from core.pjl import coletar_identificacao
from core.snmp import coletar_supplies
from core.asset import salvar_ativo


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PRINTER_DATA = BASE_DIR / "printer_data.json"


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
# NORMALIZAÇÃO DA IDENTIFICAÇÃO
# ============================================================

def normalizar_identificacao(dados):

    if not dados:
        return {

            "fabricante": "Desconhecido",

            "modelo": "Desconhecido",

            "familia": "",

            "tipo": "",

            "serial": "Desconhecido",

            "contador": None

        }


    modelo = dados.get(
        "modelo",
        "Desconhecido"
    )

    serial = dados.get(
        "serial",
        "Desconhecido"
    )

    contador = dados.get(
        "contador"
    )


    fabricante = "Desconhecido"

    texto = str(modelo).lower()


    if "lexmark" in texto:
        fabricante = "Lexmark"

    elif "brother" in texto:
        fabricante = "Brother"

    elif "canon" in texto:
        fabricante = "Canon"

    elif "hp" in texto or "hewlett" in texto:
        fabricante = "HP"


    familia = ""

    if modelo != "Desconhecido":

        partes = str(modelo).split()

        if partes:

            familia = partes[0]


    tipo = ""

    if fabricante == "Lexmark":

        tipo = "Impressora Lexmark"


        modelo_lower = str(
            modelo
        ).lower()


        if "mx" in modelo_lower:

            tipo = (
                "Multifuncional Laser Mono"
            )


        elif "ms" in modelo_lower:

            tipo = (
                "Impressora Laser Mono"
            )


    return {

        "fabricante": fabricante,

        "modelo": modelo,

        "familia": familia,

        "tipo": tipo,

        "serial": serial,

        "contador": contador

    }


# ============================================================
# NORMALIZAÇÃO DA CONECTIVIDADE
# ============================================================

def criar_conectividade(
    ip,
    pjl_ok,
    snmp_ok
):

    return {

        "ip": ip,

        "snmp": bool(snmp_ok),

        "pjl": bool(pjl_ok),

        "web": False,

        "raw": bool(pjl_ok),

        "ipp": False

    }


# ============================================================
# SALVAR SNAPSHOT
# ============================================================

def salvar_snapshot(
    ip,
    identificacao,
    supplies,
    conectividade
):

    dados = {

        "data":
            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "ip":
            ip,

        "identificacao":
            identificacao,

        "conectividade":
            conectividade,

        "supplies":
            supplies

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
    identificacao,
    supplies,
    conectividade
):

    print()

    print("=" * 60)

    print(
        "RESUMO DA IMPRESSORA"
    )

    print("=" * 60)


    print()

    print(
        "IP:",
        conectividade["ip"]
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
        "Serial:",
        identificacao["serial"]
    )

    print(
        "Contador:",
        identificacao["contador"]
    )


    print()

    print(
        "SNMP:",
        "ATIVO"
        if conectividade["snmp"]
        else "INATIVO"
    )

    print(
        "PJL:",
        "ATIVO"
        if conectividade["pjl"]
        else "INATIVO"
    )


    print()

    print(
        "Suprimentos monitorados:",
        len(supplies)
    )


    print()

    print("=" * 60)

    print(
        "SUPRIMENTOS MONITORADOS"
    )

    print("=" * 60)


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
            item.get(
                "capacidade"
            )
        )

        print(
            "    Restante:",
            item.get(
                "restante"
            )
        )

        print(
            "    Consumido:",
            item.get(
                "consumido"
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


    # --------------------------------------------------------
    # PJL
    # --------------------------------------------------------

    print()

    print(
        "[1/2] Coletando identificação via PJL..."
    )


    try:

        identificacao_bruta = (
            await coletar_identificacao(ip)
        )

        pjl_ok = bool(
            identificacao_bruta
        )

    except Exception as erro:

        print(
            "Aviso PJL:",
            erro
        )

        identificacao_bruta = {}

        pjl_ok = False


    identificacao = (
        normalizar_identificacao(
            identificacao_bruta
        )
    )


    # --------------------------------------------------------
    # SNMP
    # --------------------------------------------------------

    print()

    print(
        "[2/2] Coletando suprimentos via SNMP..."
    )


    try:

        supplies = await coletar_supplies(
            ip
        )

        snmp_ok = bool(
            supplies
        )

    except Exception as erro:

        print(
            "Aviso SNMP:",
            erro
        )

        supplies = []

        snmp_ok = False


    # --------------------------------------------------------
    # Conectividade
    # --------------------------------------------------------

    conectividade = criar_conectividade(

        ip,

        pjl_ok,

        snmp_ok

    )


    # --------------------------------------------------------
    # Snapshot
    # --------------------------------------------------------

    dados_snapshot = salvar_snapshot(

        ip,

        identificacao,

        supplies,

        conectividade

    )


    # --------------------------------------------------------
    # Ativo
    # --------------------------------------------------------

    ativo_salvo = False


    if identificacao.get(
        "serial"
    ) not in (
        None,
        "",
        "Desconhecido"
    ):

        try:

            salvar_ativo(

                identificacao,

                conectividade,

                supplies

            )

            ativo_salvo = True

        except Exception as erro:

            print()

            print(
                "Aviso ao salvar ativo:",
                erro
            )


    # --------------------------------------------------------
    # RESUMO
    # --------------------------------------------------------

    exibir_resumo(

        identificacao,

        supplies,

        conectividade

    )


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