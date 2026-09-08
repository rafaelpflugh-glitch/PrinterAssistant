from core.session import Session
from core.commands import Commands


def main():

    session = Session()

    session.connect(
        "192.168.14.134"
    )

    commands = Commands(
        session
    )

    print()
    print("=" * 70)
    print("COMANDOS DISPONIVEIS")
    print("=" * 70)

    for nome in commands.listar():

        print(
            f" - {nome}"
        )

    print()

    # ========================================================
    # RELATORIO DE CONFIGURACAO
    # ========================================================

    resultado = commands.executar(
        "print_configuration"
    )

    print()

    print("=" * 70)
    print("RESULTADO CONFIGURATION")
    print("=" * 70)

    print(
        "Sucesso:",
        resultado.get(
            "success"
        )
    )

    print(
        "HTTP:",
        resultado.get(
            "status_code"
        )
    )

    # ========================================================
    # RELATORIO DE ESTATISTICAS
    # ========================================================

    resultado = commands.executar(
        "print_statistics"
    )

    print()

    print("=" * 70)
    print("RESULTADO STATISTICS")
    print("=" * 70)

    print(
        "Sucesso:",
        resultado.get(
            "success"
        )
    )

    print(
        "HTTP:",
        resultado.get(
            "status_code"
        )
    )


if __name__ == "__main__":

    main()