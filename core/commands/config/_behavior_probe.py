"""
Printer Assistant - PJL Behavior Probe

Teste controlado do comportamento de jobs PJL.

O objetivo é verificar se os DEFAULTs configurados
pela impressora realmente influenciam um job enviado
sem sobrescrever essas configurações no próprio job.

Este módulo imprime uma página de teste.

As configurações são restauradas ao final.
"""

import socket
import time


VARIABLES = [
    {
        "name": "DUPLEX",
        "test": "ON",
    },
    {
        "name": "RESOLUTION",
        "test": "1200",
    },
    {
        "name": "ORIENTATION",
        "test": "LANDSCAPE",
    },
    {
        "name": "DENSITY",
        "test": "4",
    },
]


class PJLJobConnection:
    def __init__(
        self,
        ip,
        port=9100,
        timeout=5,
    ):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def enviar(
        self,
        dados,
    ):
        inicio = time.monotonic()

        with socket.create_connection(
            (self.ip, self.port),
            timeout=self.timeout,
        ) as sock:

            sock.settimeout(self.timeout)

            if isinstance(dados, str):
                dados = dados.encode(
                    "ascii",
                    errors="replace",
                )

            sock.sendall(dados)

        return {
            "bytes": len(dados),
            "tempo": (
                time.monotonic()
                - inicio
            ),
        }


def enviar_pjl(
    ip,
    comando,
    port=9100,
    timeout=5,
):
    if not comando.endswith("\r\n"):
        comando += "\r\n"

    with socket.create_connection(
        (ip, port),
        timeout=timeout,
    ) as sock:

        sock.settimeout(timeout)

        sock.sendall(
            comando.encode(
                "ascii",
                errors="replace",
            )
        )

        time.sleep(0.15)

        resposta = bytearray()

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                resposta.extend(bloco)

                if len(bloco) < 4096:
                    break

            except socket.timeout:
                break

    return resposta.decode(
        "latin-1",
        errors="replace",
    )


def inquire(
    ip,
    variable,
):
    resposta = enviar_pjl(
        ip,
        f"@PJL INQUIRE {variable}",
    )

    return extrair_valor(
        resposta,
        variable,
    )


def dinquire(
    ip,
    variable,
):
    resposta = enviar_pjl(
        ip,
        f"@PJL DINQUIRE {variable}",
    )

    return extrair_valor(
        resposta,
        variable,
    )


def default(
    ip,
    variable,
    value,
):
    enviar_pjl(
        ip,
        f"@PJL DEFAULT {variable}={value}",
    )


def extrair_valor(
    resposta,
    variable,
):
    if not resposta:
        return None

    linhas = resposta.splitlines()

    alvo = variable.strip().upper()

    for linha in linhas:
        linha = linha.strip()

        if not linha:
            continue

        if linha.upper().startswith("@PJL"):
            continue

        if "=" in linha:
            nome, valor = linha.split(
                "=",
                1,
            )

            if nome.strip().upper() == alvo:
                return (
                    valor
                    .strip()
                    .strip('"')
                )

        return linha.strip('"')

    return None


def criar_job_pcl():
    """
    Cria uma página PCL mínima.

    Importante:
    NÃO envia DEFAULT, SET ou RESET dentro do job.

    A intenção é deixar a impressora decidir o comportamento
    com base nos defaults previamente configurados.
    """

    partes = []

    partes.append(
        b"\x1b%-12345X"
    )

    partes.append(
        b"@PJL JOB NAME=\"PA_BEHAVIOR_PROBE\"\r\n"
    )

    partes.append(
        b"@PJL ENTER LANGUAGE=PCL\r\n"
    )

    partes.append(
        b"\x1bE"
    )

    partes.append(
        b"\x1b&l1O"
    )

    partes.append(
        b"\x1b&l6D"
    )

    partes.append(
        b"\x1b&l0E"
    )

    partes.append(
        b"\x1b&a0L"
    )

    partes.append(
        b"\x1b*p100X"
    )

    partes.append(
        b"\x1b*p100Y"
    )

    partes.append(
        b"PRINTER ASSISTANT\r\n"
    )

    partes.append(
        b"PJL DEFAULT BEHAVIOR PROBE\r\n"
    )

    partes.append(
        b"\x0c"
    )

    partes.append(
        b"\x1b%-12345X"
    )

    return b"".join(partes)


def ler_estado(
    ip,
):
    estado = {}

    for item in VARIABLES:
        nome = item["name"]

        estado[nome] = {
            "current": inquire(
                ip,
                nome,
            ),
            "default": dinquire(
                ip,
                nome,
            ),
        }

    return estado


def imprimir_estado(
    estado,
    titulo,
):
    print()
    print("=" * 72)
    print(titulo)
    print("=" * 72)

    for nome, dados in estado.items():
        print()
        print(nome)
        print(
            f"  INQUIRE  : "
            f"{dados['current']}"
        )
        print(
            f"  DINQUIRE : "
            f"{dados['default']}"
        )


def main():
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - "
        "PJL JOB BEHAVIOR PROBE"
    )
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(
        f"Impressora: {ip}"
    )
    print(
        "RAW:        9100"
    )
    print()

    print(
        "Este teste irá:"
    )

    print(
        "1. Ler o estado original."
    )

    print(
        "2. Alterar temporariamente "
        "os DEFAULTs."
    )

    print(
        "3. Enviar UMA página PCL."
    )

    print(
        "4. Restaurar os DEFAULTs."
    )

    print()

    confirmar = input(
        "A impressora irá imprimir. "
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print(
            "Teste cancelado."
        )
        return

    original = None

    try:
        original = ler_estado(
            ip
        )

        imprimir_estado(
            original,
            "1. ESTADO ORIGINAL",
        )

        print()
        print("=" * 72)
        print("2. CONFIGURANDO DEFAULTs")
        print("=" * 72)

        for item in VARIABLES:
            nome = item["name"]
            teste = item["test"]

            print()
            print(
                f"DEFAULT {nome}={teste}"
            )

            default(
                ip,
                nome,
                teste,
            )

            corrente = inquire(
                ip,
                nome,
            )

            padrao = dinquire(
                ip,
                nome,
            )

            print(
                f"  INQUIRE  : {corrente}"
            )

            print(
                f"  DINQUIRE : {padrao}"
            )

        configurado = ler_estado(
            ip
        )

        imprimir_estado(
            configurado,
            "3. DEFAULTs CONFIGURADOS",
        )

        print()
        print("=" * 72)
        print("4. ENVIO DO JOB")
        print("=" * 72)

        print()
        print(
            "O job NÃO contém comandos "
            "DEFAULT, SET ou RESET."
        )

        print(
            "A impressora deverá utilizar "
            "os DEFAULTs configurados."
        )

        input(
            "Pressione ENTER para enviar "
            "o job..."
        )

        job = criar_job_pcl()

        print()
        print(
            "Abrindo conexão RAW..."
        )

        resultado = PJLJobConnection(
            ip=ip,
            port=9100,
            timeout=5,
        ).enviar(job)

        print(
            "Job enviado."
        )

        print(
            f"Bytes enviados: "
            f"{resultado['bytes']}"
        )

        print(
            f"Tempo: "
            f"{resultado['tempo']:.3f}s"
        )

        print()
        print(
            "A página foi enviada."
        )

        print(
            "Observe fisicamente:"
        )

        print(
            "- orientação"
        )

        print(
            "- duplex"
        )

        print(
            "- resolução/densidade"
        )

        print(
            "- comportamento geral"
        )

    finally:
        if original is not None:
            print()
            print("=" * 72)
            print(
                "5. RESTAURAÇÃO"
            )
            print("=" * 72)

            for nome, dados in original.items():
                valor = dados["default"]

                if valor is None:
                    continue

                print()
                print(
                    f"Restaurando "
                    f"DEFAULT {nome}="
                    f"{valor}"
                )

                default(
                    ip,
                    nome,
                    valor,
                )

                print(
                    f"  INQUIRE  : "
                    f"{inquire(ip, nome)}"
                )

                print(
                    f"  DINQUIRE : "
                    f"{dinquire(ip, nome)}"
                )

            final = ler_estado(
                ip
            )

            imprimir_estado(
                final,
                "6. ESTADO FINAL",
            )

            print()
            print("=" * 72)
            print(
                "TESTE FINALIZADO"
            )
            print("=" * 72)

            for nome, dados in original.items():
                final_dados = final[nome]

                corrente_ok = (
                    str(
                        final_dados["current"]
                    ).upper()
                    == str(
                        dados["current"]
                    ).upper()
                )

                default_ok = (
                    str(
                        final_dados["default"]
                    ).upper()
                    == str(
                        dados["default"]
                    ).upper()
                )

                if corrente_ok and default_ok:
                    print(
                        f"✓ {nome}: "
                        "RESTAURADO"
                    )
                else:
                    print(
                        f"✗ {nome}: "
                        "RESTAURAÇÃO "
                        "DIFERENTE"
                    )

    print()
    print(
        "Conexão RAW encerrada."
    )


if __name__ == "__main__":
    main()