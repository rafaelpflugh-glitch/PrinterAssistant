"""
Printer Assistant - MX611 Configuration Discovery Probe

Descoberta SOMENTE de leitura das capacidades e variáveis
de configuração da Lexmark MX611dhe.

Este probe:

- NÃO executa SET.
- NÃO executa DEFAULT.
- NÃO executa RESET.
- NÃO envia jobs.
- NÃO altera configurações.
- Consulta INFO PJL.
- Consulta variáveis PJL candidatas.
- Organiza os resultados por categoria.

Objetivo:

Descobrir sistematicamente quais variáveis realmente
respondem na MX611dhe antes de criar comandos de alteração.
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass


# =========================================================
# CONFIGURAÇÃO
# =========================================================

PORTA_RAW = 9100
TIMEOUT = 5
TENTATIVAS = 3

UNIVERSAL_RESET = b"\x1b%-12345X"


# =========================================================
# MODELO DE RESULTADO
# =========================================================

@dataclass
class ProbeResult:

    comando: str
    resposta: str
    tempo: float
    sucesso: bool


# =========================================================
# CATEGORIAS
# =========================================================

VARIAVEIS = {

    "IMPRESSAO": [

        "DUPLEX",
        "RESOLUTION",
        "ORIENTATION",
        "COPIES",
        "DENSITY",

    ],

    "PAPEL_E_MEDIA": [

        "PAPER",
        "MEDIATYPE",
        "MEDIAWEIGHT",
        "MEDIATEXTURE",
        "PAPERLENGTH",
        "PAPERWIDTH",
        "MEDIASOURCE",
        "PAPERWEIGHT",
        "PAPERFINISH",
        "PAPERTYPE",

    ],

    "ALIMENTACAO_E_SAIDA": [

        "TRAY",
        "INPUTTRAY",
        "TRAY1",
        "TRAY2",
        "TRAY3",
        "TRAY4",
        "TRAY5",
        "MPFEEDER",
        "ENVELOPE",
        "OUTPUTBIN",

    ],

    "IDIOMA_E_REGIAO": [

        "LANG",
        "LANGUAGE",
        "TIMEZONE",
        "COUNTRY",
        "COUNTRYCODE",

    ],

    "JOB": [

        "JOBNAME",
        "USERNAME",
        "USTATUS",

    ],

    "DISPOSITIVO": [

        "DISPLAY",
        "SERIALNUMBER",
        "FIRMWARE",

    ],

    "QUALIDADE": [

        "ECOMODE",
        "TONERDARKNESS",
        "TONER_DARKNESS",
        "BRIGHTNESS",
        "CONTRAST",

    ],

    "ENERGIA": [

        "POWERSAVE",
        "POWER_SAVE",
        "SLEEP",
        "SLEEPDELAY",
        "AUTOOFF",
        "AUTO_OFF",

    ],

    "ADMINISTRACAO": [

        "PASSWORD",
        "ADMIN",
        "SECURITY",
        "LOCK",

    ],

    "SCAN_E_COPIA": [

        "SCANNER",
        "SCANNERDUPLEX",
        "SCANNER_DUPLEX",
        "SCANCOLOR",
        "SCANRESOLUTION",
        "SCAN_RESOLUTION",
        "COPY",
        "COPIES",
        "COPYDUPLEX",
        "COPY_DUPLEX",

    ],

}


# =========================================================
# COMANDOS INFO
# =========================================================

COMANDOS_INFO = [

    "@PJL INFO ID",
    "@PJL INFO CONFIG",
    "@PJL INFO STATUS",
    "@PJL INFO PAGECOUNT",
    "@PJL INFO MEMORY",
    "@PJL INFO VARIABLES",

]


# =========================================================
# FUNÇÕES DE REDE
# =========================================================

def conectar(ip: str) -> socket.socket | None:

    for tentativa in range(
        1,
        TENTATIVAS + 1,
    ):

        print(
            f"Conectando em "
            f"{ip}:{PORTA_RAW} "
            f"(tentativa "
            f"{tentativa}/{TENTATIVAS})..."
        )

        try:

            sock = socket.create_connection(
                (
                    ip,
                    PORTA_RAW,
                ),
                timeout=TIMEOUT,
            )

            sock.settimeout(
                TIMEOUT
            )

            return sock

        except Exception as erro:

            print(
                f"Falha: {erro}"
            )

            if tentativa < TENTATIVAS:

                time.sleep(0.5)

    return None


# =========================================================
# ENVIO PJL
# =========================================================

def enviar_pjl(
    ip: str,
    comando: str,
) -> ProbeResult:

    inicio = time.perf_counter()

    payload = (
        UNIVERSAL_RESET
        + comando.encode(
            "ascii",
            errors="ignore",
        )
        + b"\r\n"
        + UNIVERSAL_RESET
    )

    sock = conectar(ip)

    if sock is None:

        return ProbeResult(
            comando=comando,
            resposta="",
            tempo=(
                time.perf_counter()
                - inicio
            ),
            sucesso=False,
        )

    resposta = b""

    try:

        sock.sendall(
            payload
        )

        while True:

            try:

                parte = sock.recv(
                    4096
                )

            except socket.timeout:

                break

            if not parte:

                break

            resposta += parte

            if len(parte) < 4096:

                break

    except Exception as erro:

        resposta = (
            f"ERRO: {erro}"
            .encode(
                "latin1",
                errors="ignore",
            )
        )

    finally:

        try:

            sock.close()

        except Exception:

            pass

    tempo = (
        time.perf_counter()
        - inicio
    )

    texto = resposta.decode(
        "latin1",
        errors="ignore",
    )

    return ProbeResult(
        comando=comando,
        resposta=texto,
        tempo=tempo,
        sucesso=True,
    )


# =========================================================
# LIMPEZA DA RESPOSTA
# =========================================================

def limpar_resposta(
    resposta: str,
    comando: str,
) -> str:

    texto = resposta.replace(
        "\x00",
        "",
    )

    texto = texto.replace(
        "\x0c",
        "",
    )

    texto = texto.strip()

    linhas = []

    for linha in texto.splitlines():

        linha = linha.strip()

        if not linha:

            continue

        if linha == comando:

            continue

        if linha.startswith(
            "\x1b%-12345X"
        ):

            continue

        linhas.append(
            linha
        )

    if not linhas:

        return "(sem resposta)"

    return "\n".join(
        linhas
    )


# =========================================================
# INQUIRE
# =========================================================

def consultar_variavel(
    ip: str,
    variavel: str,
    default: bool = False,
) -> ProbeResult:

    if default:

        comando = (
            f"@PJL DINQUIRE {variavel}"
        )

    else:

        comando = (
            f"@PJL INQUIRE {variavel}"
        )

    return enviar_pjl(
        ip,
        comando,
    )


# =========================================================
# IMPRESSÃO DE RESULTADO
# =========================================================

def imprimir_resultado(
    resultado: ProbeResult,
) -> str:

    resposta = limpar_resposta(
        resultado.resposta,
        resultado.comando,
    )

    return resposta


# =========================================================
# TESTE DE VARIÁVEL
# =========================================================

def testar_variavel(
    ip: str,
    variavel: str,
) -> tuple[str, str]:

    resultado_atual = consultar_variavel(
        ip,
        variavel,
        default=False,
    )

    atual = imprimir_resultado(
        resultado_atual
    )

    resultado_default = consultar_variavel(
        ip,
        variavel,
        default=True,
    )

    padrao = imprimir_resultado(
        resultado_default
    )

    print(
        f"INQUIRE  : {atual}"
    )

    print(
        f"DINQUIRE : {padrao}"
    )

    return atual, padrao


# =========================================================
# COMANDOS INFO
# =========================================================

def consultar_info(
    ip: str,
    comando: str,
) -> str:

    resultado = enviar_pjl(
        ip,
        comando,
    )

    return imprimir_resultado(
        resultado
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 72
    )

    print(
        "PRINTER ASSISTANT - "
        "MX611 CONFIGURATION DISCOVERY PROBE"
    )

    print(
        "=" * 72
    )

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP inválido."
        )

        return

    print()

    print(
        f"Impressora: {ip}"
    )

    print(
        f"RAW:        {PORTA_RAW}"
    )

    print()

    print(
        "Este teste:"
    )

    print()

    print(
        "- NAO executa SET."
    )

    print(
        "- NAO executa DEFAULT."
    )

    print(
        "- NAO executa RESET."
    )

    print(
        "- NAO envia jobs."
    )

    print(
        "- NAO altera configuracoes."
    )

    print()

    print(
        "Serão somente consultadas "
        "informações PJL."
    )

    print()

    continuar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if continuar != "S":

        print(
            "Teste cancelado."
        )

        return

    # =====================================================
    # INFO
    # =====================================================

    print()
    print(
        "=" * 72
    )
    print(
        "1. INFORMACOES DA IMPRESSORA"
    )
    print(
        "=" * 72
    )

    for comando in COMANDOS_INFO:

        print()
        print(
            "-" * 72
        )

        print(
            comando
        )

        print(
            "-" * 72
        )

        resultado = enviar_pjl(
            ip,
            comando,
        )

        resposta = imprimir_resultado(
            resultado
        )

        print(
            resposta
        )

    # =====================================================
    # VARIAVEIS
    # =====================================================

    print()
    print(
        "=" * 72
    )
    print(
        "2. DESCOBERTA DE VARIAVEIS"
    )
    print(
        "=" * 72
    )

    resultados = {}

    for categoria, lista in VARIAVEIS.items():

        print()
        print(
            "=" * 72
        )

        print(
            f"CATEGORIA: {categoria}"
        )

        print(
            "=" * 72
        )

        resultados[categoria] = {}

        for variavel in lista:

            print()
            print(
                f"## VARIAVEL: {variavel}"
            )

            print()

            atual, padrao = testar_variavel(
                ip,
                variavel,
            )

            resultados[categoria][
                variavel
            ] = {
                "current": atual,
                "default": padrao,
            }

    # =====================================================
    # RESUMO
    # =====================================================

    print()
    print(
        "=" * 72
    )
    print(
        "3. RESUMO DA DESCOBERTA"
    )
    print(
        "=" * 72
    )

    for categoria, dados in resultados.items():

        print()
        print(
            f"[{categoria}]"
        )

        for variavel, valores in dados.items():

            atual = valores[
                "current"
            ]

            padrao = valores[
                "default"
            ]

            if (
                atual != "(sem resposta)"
                or padrao != "(sem resposta)"
            ):

                print(
                    f"{variavel:<20} "
                    f"CURRENT={atual:<20} "
                    f"DEFAULT={padrao}"
                )

    print()
    print(
        "=" * 72
    )

    print(
        "DESCOBERTA CONCLUIDA."
    )

    print()

    print(
        "Nenhuma configuracao foi alterada."
    )

    print(
        "Nenhum DEFAULT foi alterado."
    )

    print(
        "Nenhum job foi enviado."
    )

    print()

    print(
        "As variaveis que responderem "
        "com valores reais serao candidatas "
        "para probes SET/DEFAULT/RESET."
    )

    print()

    print(
        "Variaveis que retornarem "
        '"?" ou respostas vazias nao serao '
        "consideradas suportadas ainda."
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":

    main()