import asyncio
import json

from modules.discovery import descobrir
from modules.inventory import inventariar_lista
from modules.diagnostic import diagnosticar

from core.session import criar_sessao

from tools.registry import ToolRegistry


# ==========================================================
# EQUIPAMENTO
# ==========================================================

def mostrar_equipamento(device):

    dados = device.to_dict()

    ident = dados.get("identificacao", {})
    conexao = dados.get("conectividade", {})
    supplies = dados.get("supplies", [])

    print()
    print("=" * 70)
    print("IMPRESSORA")
    print("=" * 70)

    print("Fabricante :", ident.get("fabricante"))
    print("Modelo     :", ident.get("modelo"))
    print("Família    :", ident.get("familia"))
    print("Tipo       :", ident.get("tipo"))
    print("Serial     :", ident.get("serial"))

    contador = ident.get("contador")

    if contador is None:
        contador = "N/A"
    else:
        contador = f"{contador:,}".replace(",", ".")

    print("Contador   :", contador)

    print()
    print("Conectividade")

    for chave, valor in conexao.items():

        if isinstance(valor, bool):
            valor = "ATIVO" if valor else "INATIVO"

        print(f"  {chave.upper():12}: {valor}")

    print()
    print("Suprimentos")

    if not supplies:

        print("Nenhum")

    else:

        for s in supplies:

            print(
                f"- {s['nome']} | "
                f"{s['nivel']}% | "
                f"{s['status']}"
            )

    print()
    print("=" * 70)


# ==========================================================
# MENU IMPRESSORAS
# ==========================================================

def menu_impressoras(lista):

    print()

    print("=" * 70)
    print("IMPRESSORAS")
    print("=" * 70)

    for i, p in enumerate(lista, 1):

        print(
            f"[{i}] {p.modelo()} - {p.ip}"
        )

    print()

    try:

        escolha = int(
            input("> ")
        )

        return lista[escolha - 1]

    except:

        return None


# ==========================================================
# DIAGNÓSTICO
# ==========================================================

def mostrar_diagnostico(resultado):

    print()

    print("=" * 70)
    print("DIAGNÓSTICO")
    print("=" * 70)

    for chave, valor in resultado.items():

        if chave == "alertas":
            continue

        print(f"{chave.upper():15}: {valor}")

    print()

    print("Alertas")

    if resultado["alertas"]:

        for alerta in resultado["alertas"]:

            print("[!]", alerta)

    else:

        print("Nenhum")

    print("=" * 70)


# ==========================================================
# BACKUP
# ==========================================================

def salvar(device):

    with open(

        "selected_printer.json",

        "w",

        encoding="utf8"

    ) as arq:

        json.dump(

            device.to_dict(),

            arq,

            indent=4,

            ensure_ascii=False

        )


# ==========================================================
# TOOLS
# ==========================================================

def menu_tools(registry):

    while True:

        print()

        print("=" * 70)
        print("FERRAMENTAS")
        print("=" * 70)

        registry.show()

        print("[0] Sair")

        print()

        op = input("> ").strip()

        if op == "0":
            break

        registry.execute(op)


# ==========================================================
# MAIN
# ==========================================================

async def main():

    print()

    print("=" * 70)
    print("PRINTER ASSISTANT")
    print("=" * 70)

    impressoras = await descobrir("192.168.14")

    if not impressoras:

        print("Nenhuma impressora encontrada.")

        return

    await inventariar_lista(impressoras)

    selecionada = menu_impressoras(impressoras)

    if selecionada is None:

        print("Cancelado.")

        return

    mostrar_equipamento(selecionada)

    sessao = criar_sessao()

    sessao.ativar(selecionada)

    resultado = diagnosticar(sessao)

    mostrar_diagnostico(resultado)

    salvar(selecionada)

    registry = ToolRegistry(sessao)

    menu_tools(registry)


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()

        print("Encerrado.")