"""
Printer Assistant - PJL Persistent Write Probe 2

Segunda bateria controlada de testes de configuração PJL.

Este módulo testa DEFAULT em variáveis simples e reversíveis.
Cada variável:
    1. descobre o valor corrente;
    2. descobre o valor default;
    3. aplica um valor alternativo;
    4. verifica INQUIRE;
    5. verifica DINQUIRE;
    6. restaura o valor original;
    7. verifica a restauração.

Nenhuma variável deve permanecer alterada ao final do teste.
"""

from core.commands.config_writer import PJLWriter


TESTES = [
    {
        "variavel": "PAPER",
        "teste": "LETTER",
    },
    {
        "variavel": "MEDIATYPE",
        "teste": "CARDSTOCK",
    },
    {
        "variavel": "PERSONALITY",
        "teste": "PCL",
    },
    {
        "variavel": "POWERSAVE",
        "teste": "OFF",
    },
    {
        "variavel": "ECONOMODE",
        "teste": "ON",
    },
    {
        "variavel": "PAGEPROTECT",
        "teste": "ON",
    },
    {
        "variavel": "RESOURCESAVE",
        "teste": "ON",
    },
    {
        "variavel": "WIDEA4",
        "teste": "YES",
    },
    {
        "variavel": "MPTRAY",
        "teste": "MANUAL",
    },
    {
        "variavel": "BINDING",
        "teste": "SHORTEDGE",
    },
    {
        "variavel": "REPRINT",
        "teste": "ON",
    },
]


def normalizar(valor):
    if valor is None:
        return None

    return str(valor).strip().strip('"').upper()


def consultar(writer, variavel, tipo):
    if tipo == "INQUIRE":
        return writer.inquire(variavel)

    if tipo == "DINQUIRE":
        return writer.dinquire(variavel)

    raise ValueError(f"Tipo de consulta inválido: {tipo}")


def testar_variavel(writer, variavel, valor_teste):
    print()
    print("=" * 72)
    print(f"VARIÁVEL: {variavel}")
    print("=" * 72)

    # ----------------------------------------------------------
    # ESTADO INICIAL
    # ----------------------------------------------------------

    print()
    print(f"INQUIRE {variavel}")

    original_corrente = writer.inquire(variavel)

    print(
        f"Valor corrente original: "
        f"{original_corrente}"
    )

    print()
    print(f"DINQUIRE {variavel}")

    original_default = writer.dinquire(variavel)

    print(
        f"Valor default original:  "
        f"{original_default}"
    )

    if original_corrente is None:
        print()
        print("⚠ Não foi possível descobrir o valor corrente.")
        print("Teste ignorado para esta variável.")
        return {
            "variavel": variavel,
            "status": "IGNORADO",
            "motivo": "INQUIRE sem resposta",
        }

    if original_default is None:
        print()
        print("⚠ Não foi possível descobrir o valor default.")
        print("Teste ignorado para esta variável.")
        return {
            "variavel": variavel,
            "status": "IGNORADO",
            "motivo": "DINQUIRE sem resposta",
        }

    print()
    print(f"Valor de teste: {valor_teste}")

    # ----------------------------------------------------------
    # APLICA DEFAULT
    # ----------------------------------------------------------

    print()
    print("-" * 72)
    print(f"1. DEFAULT {variavel}={valor_teste}")
    print("-" * 72)

    resposta = writer.default(
        variavel,
        valor_teste,
    )

    if resposta:
        print()
        print("Resposta PJL:")
        print(resposta)
    else:
        print()
        print("(sem resposta PJL esperada)")

    # ----------------------------------------------------------
    # VERIFICA INQUIRE
    # ----------------------------------------------------------

    print()
    print(f"INQUIRE {variavel} após DEFAULT")

    depois_corrente = writer.inquire(variavel)

    print(
        f"Valor corrente: "
        f"{depois_corrente}"
    )

    # ----------------------------------------------------------
    # VERIFICA DINQUIRE
    # ----------------------------------------------------------

    print()
    print(f"DINQUIRE {variavel} após DEFAULT")

    depois_default = writer.dinquire(variavel)

    print(
        f"Valor default:  "
        f"{depois_default}"
    )

    corrente_ok = (
        normalizar(depois_corrente)
        == normalizar(valor_teste)
    )

    default_ok = (
        normalizar(depois_default)
        == normalizar(valor_teste)
    )

    if corrente_ok:
        print()
        print(
            f"✓ INQUIRE confirmou "
            f"{variavel}={valor_teste}"
        )
    else:
        print()
        print(
            f"⚠ INQUIRE NÃO confirmou "
            f"{variavel}={valor_teste}"
        )

    if default_ok:
        print()
        print(
            f"✓ DINQUIRE confirmou "
            f"{variavel}={valor_teste}"
        )
    else:
        print()
        print(
            f"⚠ DINQUIRE NÃO confirmou "
            f"{variavel}={valor_teste}"
        )

    # ----------------------------------------------------------
    # RESTAURAÇÃO
    # ----------------------------------------------------------

    print()
    print("-" * 72)
    print(
        f"2. RESTAURANDO "
        f"DEFAULT {variavel}={original_default}"
    )
    print("-" * 72)

    resposta_restauracao = writer.default(
        variavel,
        original_default,
    )

    if resposta_restauracao:
        print()
        print("Resposta PJL:")
        print(resposta_restauracao)
    else:
        print()
        print("(sem resposta PJL esperada)")

    # ----------------------------------------------------------
    # VERIFICA RESTAURAÇÃO
    # ----------------------------------------------------------

    print()
    print(f"INQUIRE {variavel} final")

    final_corrente = writer.inquire(variavel)

    print(
        f"Valor corrente final: "
        f"{final_corrente}"
    )

    print()
    print(f"DINQUIRE {variavel} final")

    final_default = writer.dinquire(variavel)

    print(
        f"Valor default final:  "
        f"{final_default}"
    )

    corrente_restaurado = (
        normalizar(final_corrente)
        == normalizar(original_corrente)
    )

    default_restaurado = (
        normalizar(final_default)
        == normalizar(original_default)
    )

    if corrente_restaurado:
        print()
        print("✓ INQUIRE restaurado.")
    else:
        print()
        print("⚠ INQUIRE NÃO foi restaurado.")

    if default_restaurado:
        print()
        print("✓ DINQUIRE restaurado.")
    else:
        print()
        print("⚠ DINQUIRE NÃO foi restaurado.")

    # ----------------------------------------------------------
    # RESULTADO
    # ----------------------------------------------------------

    sucesso = (
        corrente_ok
        and default_ok
        and corrente_restaurado
        and default_restaurado
    )

    print()
    print("-" * 72)
    print("RESULTADO")
    print("-" * 72)

    print(
        f"Original corrente : "
        f"{original_corrente}"
    )

    print(
        f"Original default  : "
        f"{original_default}"
    )

    print(
        f"Valor testado     : "
        f"{valor_teste}"
    )

    print(
        f"Após DEFAULT INQ  : "
        f"{depois_corrente}"
    )

    print(
        f"Após DEFAULT DINQ : "
        f"{depois_default}"
    )

    print(
        f"Final corrente    : "
        f"{final_corrente}"
    )

    print(
        f"Final default     : "
        f"{final_default}"
    )

    if sucesso:
        print()
        print(
            f"✓ {variavel}: "
            f"DEFAULT CONFIRMADO"
        )

        status = "CONFIRMADO"
    else:
        print()
        print(
            f"⚠ {variavel}: "
            f"DEFAULT NÃO CONFIRMADO"
        )

        status = "FALHOU"

    return {
        "variavel": variavel,
        "status": status,
        "original_corrente": original_corrente,
        "original_default": original_default,
        "valor_teste": valor_teste,
        "depois_corrente": depois_corrente,
        "depois_default": depois_default,
        "final_corrente": final_corrente,
        "final_default": final_default,
        "corrente_ok": corrente_ok,
        "default_ok": default_ok,
        "corrente_restaurado": corrente_restaurado,
        "default_restaurado": default_restaurado,
    }


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL PERSISTENT WRITE PROBE 2")
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(f"Impressora: {ip}")
    print("RAW:        9100")

    print()
    print("Variáveis desta bateria:")

    for teste in TESTES:
        print(
            f"- {teste['variavel']} "
            f"-> {teste['teste']}"
        )

    print()
    print("IMPORTANTE:")
    print(
        "Cada variável será alterada individualmente."
    )
    print(
        "O valor original será descoberto antes do teste."
    )
    print(
        "Após o teste, o valor original será restaurado."
    )
    print()
    print(
        "Se uma variável falhar, o teste continua "
        "para as próximas."
    )

    print()
    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    writer = PJLWriter(
        ip=ip,
        port=9100,
        timeout=5,
    )

    resultados = []

    try:
        writer.conectar()

        print()
        print("Conectado.")

        for teste in TESTES:
            resultado = testar_variavel(
                writer=writer,
                variavel=teste["variavel"],
                valor_teste=teste["teste"],
            )

            resultados.append(resultado)

    finally:
        writer.fechar()

    # ----------------------------------------------------------
    # RESUMO FINAL
    # ----------------------------------------------------------

    print()
    print()
    print("=" * 72)
    print("RESUMO FINAL")
    print("=" * 72)

    confirmados = 0
    falhas = 0
    ignorados = 0

    for resultado in resultados:
        variavel = resultado["variavel"]
        status = resultado["status"]

        print(
            f"{variavel:20} "
            f"{status}"
        )

        if status == "CONFIRMADO":
            confirmados += 1

        elif status == "FALHOU":
            falhas += 1

        else:
            ignorados += 1

    print()
    print(
        f"DEFAULT confirmado : {confirmados}"
    )

    print(
        f"Falhas              : {falhas}"
    )

    print(
        f"Ignorados           : {ignorados}"
    )

    print()
    print(
        "Nenhuma variável deve permanecer "
        "alterada pelo teste."
    )

    print()


if __name__ == "__main__":
    main()