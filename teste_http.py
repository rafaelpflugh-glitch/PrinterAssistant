from core.session import Session
from core.executor import Executor


def main():

    session = Session()

    session.connect(
        "192.168.14.134"
    )

    executor = Executor(
        session
    )

    resultado = executor.get(
        "/cgi-bin/dynamic/printer/PrinterStatus.html"
    )

    print()
    print("=" * 70)
    print("RESULTADO")
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

    print(
        "URL:",
        resultado.get(
            "url"
        )
    )

    print()
    print(
        "Primeiros 500 caracteres:"
    )

    print(
        resultado.get(
            "text",
            ""
        )[:500]
    )

    print()


if __name__ == "__main__":

    main()