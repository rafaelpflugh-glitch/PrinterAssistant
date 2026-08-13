"""
Printer Assistant - MX611 PJL Capability Discovery Probe

Descobre sistematicamente quais variáveis PJL documentadas
respondem na Lexmark MX611.

IMPORTANTE:
- NÃO executa SET.
- NÃO executa DEFAULT.
- NÃO executa RESET.
- NÃO envia jobs.
- NÃO altera configurações.

O probe diferencia:
    SUPPORTED_VALUE
    UNKNOWN
    EMPTY_OR_NULL
    ECHOED_COMMAND

A classificação UNKNOWN ocorre quando a impressora devolve
o próprio comando INQUIRE/DINQUIRE em vez de um valor.
"""

import socket
import time


RAW_PORT = 9100
CONNECT_TIMEOUT = 3.0
RETRIES = 3


# ----------------------------------------------------------------------
# VARIÁVEIS PJL COMUNS
# Documentadas para a família MX610/MX611.
# ----------------------------------------------------------------------

COMMON_VARIABLES = [
    "AUTOCONT",
    "BINDING",
    "BITSPERPIXEL",
    "CLEARABLEWARNINGS",
    "COPIES",
    "CPLOCK",
    "DENSITY",
    "DUPLEX",
    "ECONOMODE",
    "FORMLINES",
    "LANG",
    "LOWTONER",
    "MANUALFEED",
    "MEDIATYPE",
    "ORIENTATION",
    "PAPER",
    "PAPERLENGTH",
    "PAPERWIDTH",
    "RESOLUTION",
]


# ----------------------------------------------------------------------
# VARIÁVEIS PJL ESPECÍFICAS DA LEXMARK
#
# A documentação da Lexmark lista diversas variáveis L* para MX610/MX611.
# Nesta primeira bateria estamos interessados principalmente em:
#
#   - associação de bandejas
#   - Bond
#   - Colored
#   - Custom Types
#
# Ainda não vamos alterar nenhuma delas.
# ----------------------------------------------------------------------

LEXMARK_VARIABLES = [
    # Feeders / trays
    "LASSIGNFEEDER",
    "LASSIGNMANUALENVELOPE",
    "LASSIGNMANUALPAPER",
    "LASSIGNMPFEEDER",
    "LASSIGNTRAY1",
    "LASSIGNTRAY2",
    "LASSIGNTRAY3",
    "LASSIGNTRAY4",
    "LASSIGNTRAY5",

    # Bond
    "LBONDLOADING",
    "LBONDTEXTURE",
    "LBONDWEIGHT",

    # Colored
    "LCOLOREDLOADING",
    "LCOLOREDTEXTURE",
    "LCOLOREDWEIGHT",

    # Custom paper
    "LCUSTOMPAPERFEED",
    "LCUSTOMPAPERHEIGHT",
    "LCUSTOMPAPERUNITS",
    "LCUSTOMPAPERWIDTH",

    # Custom Type 1
    "LCUSTOMTYPE1LENGTH",
    "LCUSTOMTYPE1LOADING",
    "LCUSTOMTYPE1MEDIA",
    "LCUSTOMTYPE1NAME",
    "LCUSTOMTYPE1TEXTURE",
    "LCUSTOMTYPE1WEIGHT",

    # Custom Type 2
    "LCUSTOMTYPE2LENGTH",
    "LCUSTOMTYPE2LOADING",
    "LCUSTOMTYPE2MEDIA",
    "LCUSTOMTYPE2NAME",
    "LCUSTOMTYPE2TEXTURE",
    "LCUSTOMTYPE2WEIGHT",

    # Custom Type 3
    "LCUSTOMTYPE3LENGTH",
    "LCUSTOMTYPE3LOADING",
    "LCUSTOMTYPE3MEDIA",
    "LCUSTOMTYPE3NAME",
    "LCUSTOMTYPE3TEXTURE",
    "LCUSTOMTYPE3WEIGHT",

    # Custom Type 4
    "LCUSTOMTYPE4LENGTH",
    "LCUSTOMTYPE4LOADING",
    "LCUSTOMTYPE4MEDIA",
    "LCUSTOMTYPE4NAME",
    "LCUSTOMTYPE4TEXTURE",
    "LCUSTOMTYPE4WEIGHT",

    # Custom Type 5
    "LCUSTOMTYPE5LENGTH",
    "LCUSTOMTYPE5LOADING",
    "LCUSTOMTYPE5MEDIA",
    "LCUSTOMTYPE5NAME",
    "LCUSTOMTYPE5TEXTURE",
    "LCUSTOMTYPE5WEIGHT",

    # Custom Type 6
    "LCUSTOMTYPE6LENGTH",
    "LCUSTOMTYPE6LOADING",
    "LCUSTOMTYPE6MEDIA",
    "LCUSTOMTYPE6NAME",
    "LCUSTOMTYPE6TEXTURE",
    "LCUSTOMTYPE6WEIGHT",

    # Duplex-related margins
    "LDUPLEXLEFTMARGINOFFSET",
    "LDUPLEXTOPMARGINOFFSET",

    # Envelope
    "LENVELOPETEXTURE",
    "LENVELOPEWEIGHT",

    # General Lexmark options
    "LECOMODE",
]


# ----------------------------------------------------------------------
# UTILITÁRIOS
# ----------------------------------------------------------------------

def clean_response(data: bytes) -> str:
    if not data:
        return ""

    text = data.decode("latin-1", errors="replace")

    text = text.replace("\x0c", "")
    text = text.replace("\x00", "")
    text = text.strip()

    return text


def is_echoed_command(response: str, command: str) -> bool:
    """
    Algumas variáveis não suportadas fazem a impressora devolver
    o próprio comando PJL em vez de um valor.

    Exemplo:

        @PJL INQUIRE JOBNAME

    em vez de:

        algum_valor
    """

    normalized_response = response.strip().upper()
    normalized_command = command.strip().upper()

    return normalized_response == normalized_command


def classify_response(response: str, command: str) -> str:
    if not response:
        return "NO_RESPONSE"

    if is_echoed_command(response, command):
        return "ECHOED_COMMAND"

    if response.strip() == '"?"':
        return "UNKNOWN"

    return "SUPPORTED_VALUE"


def connect(ip: str) -> socket.socket:
    last_error = None

    for attempt in range(1, RETRIES + 1):
        print(
            f"Conectando em {ip}:{RAW_PORT} "
            f"(tentativa {attempt}/{RETRIES})..."
        )

        try:
            sock = socket.create_connection(
                (ip, RAW_PORT),
                timeout=CONNECT_TIMEOUT,
            )

            sock.settimeout(1.5)

            return sock

        except OSError as exc:
            last_error = exc

            if attempt < RETRIES:
                time.sleep(0.5)

    raise ConnectionError(
        f"Não foi possível conectar em {ip}:{RAW_PORT}: {last_error}"
    )


def query(ip: str, variable: str, dynamic: bool = False):
    command_name = "DINQUIRE" if dynamic else "INQUIRE"

    command = f"@PJL {command_name} {variable}\r\n"

    start = time.perf_counter()

    try:
        sock = connect(ip)

        sock.sendall(command.encode("ascii"))

        chunks = []

        while True:
            try:
                data = sock.recv(4096)

                if not data:
                    break

                chunks.append(data)

                if len(data) < 4096:
                    break

            except socket.timeout:
                break

        sock.close()

        elapsed = time.perf_counter() - start

        response = clean_response(b"".join(chunks))

        status = classify_response(response, command)

        return response, elapsed, status

    except Exception as exc:
        elapsed = time.perf_counter() - start

        return (
            f"[ERRO: {exc}]",
            elapsed,
            "ERROR",
        )


def print_result(
    variable: str,
    current_response: str,
    current_time: float,
    current_status: str,
    default_response: str,
    default_time: float,
    default_status: str,
):
    print()
    print("-" * 72)
    print(f"VARIÁVEL: {variable}")
    print("-" * 72)

    print(f"INQUIRE")
    print(f"  Valor : {current_response or '(sem resposta)'}")
    print(f"  Tempo : {current_time:.3f}s")
    print(f"  Tipo  : {current_status}")

    print()

    print(f"DINQUIRE")
    print(f"  Valor : {default_response or '(sem resposta)'}")
    print(f"  Tempo : {default_time:.3f}s")
    print(f"  Tipo  : {default_status}")


def discover_variable(ip: str, variable: str):
    current_response, current_time, current_status = query(
        ip,
        variable,
        dynamic=False,
    )

    default_response, default_time, default_status = query(
        ip,
        variable,
        dynamic=True,
    )

    print_result(
        variable,
        current_response,
        current_time,
        current_status,
        default_response,
        default_time,
        default_status,
    )

    return {
        "variable": variable,
        "inquire": current_response,
        "inquire_time": current_time,
        "inquire_status": current_status,
        "dinquire": default_response,
        "dinquire_time": default_time,
        "dinquire_status": default_status,
    }


def print_summary(results):
    print()
    print("=" * 72)
    print("RESUMO DA DESCOBERTA")
    print("=" * 72)

    supported = []
    unknown = []
    echoed = []
    no_response = []
    errors = []

    for result in results:
        variable = result["variable"]

        statuses = {
            result["inquire_status"],
            result["dinquire_status"],
        }

        if "ERROR" in statuses:
            errors.append(variable)

        elif "NO_RESPONSE" in statuses:
            no_response.append(variable)

        elif "ECHOED_COMMAND" in statuses:
            echoed.append(variable)

        elif "UNKNOWN" in statuses:
            unknown.append(variable)

        else:
            supported.append(variable)

    print()
    print(f"SUPORTADAS / VALOR       : {len(supported)}")
    for variable in supported:
        print(f"  ✓ {variable}")

    print()
    print(f"DESCONHECIDAS / '?'      : {len(unknown)}")
    for variable in unknown:
        print(f"  ? {variable}")

    print()
    print(f"COMANDO DEVOLVIDO        : {len(echoed)}")
    for variable in echoed:
        print(f"  ↩ {variable}")

    print()
    print(f"SEM RESPOSTA             : {len(no_response)}")
    for variable in no_response:
        print(f"  - {variable}")

    print()
    print(f"ERROS                     : {len(errors)}")
    for variable in errors:
        print(f"  ✗ {variable}")

    print()
    print("=" * 72)
    print("INTERPRETAÇÃO")
    print("=" * 72)

    print()
    print("✓ SUPORTADAS / VALOR")
    print("  A impressora devolveu um valor diferente de '?'.")
    print("  Essas variáveis entram na próxima fase de validação.")

    print()
    print("? DESCONHECIDAS / '?'")
    print("  A impressora respondeu '?' para a consulta.")
    print("  Não vamos assumir que a variável seja suportada.")

    print()
    print("↩ COMANDO DEVOLVIDO")
    print("  A impressora devolveu o próprio comando.")
    print("  Isso normalmente indica que o nome não foi reconhecido.")

    print()
    print("-" * 72)
    print("NENHUMA CONFIGURAÇÃO FOI ALTERADA.")
    print("NENHUM DEFAULT FOI ALTERADO.")
    print("NENHUM JOB FOI ENVIADO.")
    print("-" * 72)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 PJL CAPABILITY DISCOVERY")
    print("=" * 72)

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {RAW_PORT}")

    print()
    print("Este teste:")
    print()
    print("- NÃO executa SET.")
    print("- NÃO executa DEFAULT.")
    print("- NÃO executa RESET.")
    print("- NÃO envia jobs.")
    print("- NÃO altera configurações.")
    print()
    print("Serão consultadas variáveis PJL documentadas")
    print("para a família Lexmark MX610/MX611.")
    print()

    confirm = input("Continuar? [S/N]: ").strip().upper()

    if confirm != "S":
        print("Teste cancelado.")
        return

    variables = COMMON_VARIABLES + LEXMARK_VARIABLES

    # Remove duplicatas preservando a ordem.
    variables = list(dict.fromkeys(variables))

    results = []

    print()
    print("=" * 72)
    print("INICIANDO DESCOBERTA")
    print("=" * 72)

    print()
    print(f"Total de variáveis: {len(variables)}")

    for index, variable in enumerate(variables, start=1):
        print()
        print("=" * 72)
        print(f"[{index}/{len(variables)}] CONSULTANDO {variable}")
        print("=" * 72)

        result = discover_variable(ip, variable)

        results.append(result)

    print_summary(results)

    print()
    print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()