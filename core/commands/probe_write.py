"""
Printer Assistant - PJL WRITE PROBE 3

Teste controlado de escrita PJL.

Objetivo:
    Descobrir exatamente o efeito de:

        @PJL SET DENSITY=4

    usando DINQUIRE para verificar o valor.

Não utiliza INFO VARIABLES durante o teste,
para evitar misturar respostas diferentes.

IMPORTANTE:
    Este teste NÃO tenta gravar configuração
    permanente/NVRAM.

Ele testa somente o estado da sessão PJL.
"""

import socket


PORTA_RAW = 9100
TIMEOUT = 5

UNIVERSAL_RESET = b"\x1b%-12345X"


def enviar_pjl(sock, comando, esperar_resposta=True):
    """
    Envia um comando PJL pela conexão existente.

    A conexão é mantida aberta para que possamos
    observar o estado dentro da mesma sessão.
    """

    payload = (
        UNIVERSAL_RESET
        + comando.encode("ascii", errors="ignore")
        + b"\r\n"
    )

    sock.sendall(payload)

    if not esperar_resposta:
        return ""

    resposta = b""

    # Pequena janela de leitura.
    sock.settimeout(1.0)

    while True:

        try:
            parte = sock.recv(4096)

        except socket.timeout:
            break

        if not parte:
            break

        resposta += parte

        if len(parte) < 4096:
            break

    return resposta.decode(
        "latin1",
        errors="ignore",
    )


def limpar_resposta(texto):
    """
    Remove alguns elementos de controle que podem
    aparecer nas respostas PJL.
    """

    if not texto:
        return ""

    texto = texto.replace("\x0c", "")
    texto = texto.replace("\x00", "")

    return texto.strip()


def extrair_valor_dinquire(resposta):
    """
    Tenta extrair o valor retornado por:

        @PJL DINQUIRE DENSITY

    Exemplo:

        3

    ou:

        @PJL DINQUIRE DENSITY
        4
    """

    resposta = limpar_resposta(resposta)

    if not resposta:
        return None

    linhas = [
        linha.strip()
        for linha in resposta.splitlines()
        if linha.strip()
    ]

    # Procuramos primeiro uma linha contendo somente
    # um número.
    for linha in reversed(linhas):

        if linha.isdigit():

            return int(linha)

    return None


def dinquire(sock, variavel):
    """
    Executa DINQUIRE e retorna:

        (resposta_bruta, valor)
    """

    comando = f"@PJL DINQUIRE {variavel}"

    resposta = enviar_pjl(
        sock,
        comando,
        esperar_resposta=True,
    )

    valor = extrair_valor_dinquire(
        resposta
    )

    return resposta, valor


def testar():
    print()
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL WRITE PROBE 3")
    print("=" * 72)
    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print("Teste controlado:")
    print()
    print("Variável : DENSITY")
    print("Teste    : 4")
    print("Original : será descoberto")
    print("Final    : restauração automática")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    sock = None

    valor_original = None

    try:

        # =================================================
        # CONEXÃO
        # =================================================

        print()
        print("Abrindo conexão RAW...")

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.settimeout(
            TIMEOUT
        )

        sock.connect(
            (
                ip,
                PORTA_RAW,
            )
        )

        print(
            f"Conectado em {ip}:{PORTA_RAW}"
        )

        # =================================================
        # 1. DINQUIRE ANTES
        # =================================================

        print()
        print("-" * 72)
        print("1. DINQUIRE ANTES")
        print("-" * 72)

        resposta, valor_original = dinquire(
            sock,
            "DENSITY",
        )

        print()
        print(
            "@PJL DINQUIRE DENSITY"
        )

        print(
            limpar_resposta(resposta)
            or "(sem resposta)"
        )

        print()
        print(
            f"Valor descoberto: "
            f"{valor_original}"
        )

        if valor_original is None:

            print()
            print(
                "Não foi possível descobrir "
                "o valor original."
            )

            return

        # =================================================
        # 2. SET
        # =================================================

        novo_valor = 4

        print()
        print("-" * 72)
        print("2. SET")
        print("-" * 72)

        comando_set = (
            f"@PJL SET DENSITY={novo_valor}"
        )

        print()
        print(
            f"Enviando: {comando_set}"
        )

        resposta_set = enviar_pjl(
            sock,
            comando_set,
            esperar_resposta=True,
        )

        print()
        print(
            "Resposta:"
        )

        print(
            limpar_resposta(
                resposta_set
            )
            or "(sem resposta)"
        )

        # =================================================
        # 3. DINQUIRE DEPOIS
        # =================================================

        print()
        print("-" * 72)
        print("3. DINQUIRE DEPOIS DO SET")
        print("-" * 72)

        resposta, valor_depois = dinquire(
            sock,
            "DENSITY",
        )

        print()
        print(
            "@PJL DINQUIRE DENSITY"
        )

        print(
            limpar_resposta(resposta)
            or "(sem resposta)"
        )

        print()
        print(
            f"Valor depois: {valor_depois}"
        )

        # =================================================
        # 4. ANÁLISE
        # =================================================

        print()
        print("-" * 72)
        print("4. RESULTADO DO TESTE")
        print("-" * 72)

        print()
        print(
            f"Original : {valor_original}"
        )

        print(
            f"Depois   : {valor_depois}"
        )

        print(
            f"Esperado : {novo_valor}"
        )

        if valor_depois == novo_valor:

            print()
            print(
                "✓ SET FUNCIONOU NA SESSÃO PJL."
            )

            print(
                "A impressora aceitou a alteração "
                "e DINQUIRE confirmou o novo valor."
            )

        elif valor_depois == valor_original:

            print()
            print(
                "⚠ SET NÃO ALTEROU O VALOR OBSERVADO."
            )

            print(
                "A impressora recebeu o comando, "
                "mas DINQUIRE voltou ao valor original."
            )

        else:

            print()
            print(
                "⚠ RESULTADO DIFERENTE DO ESPERADO."
            )

        # =================================================
        # 5. RESTAURAÇÃO
        # =================================================

        print()
        print("-" * 72)
        print("5. RESTAURAÇÃO")
        print("-" * 72)

        comando_restore = (
            f"@PJL SET DENSITY={valor_original}"
        )

        print()
        print(
            f"Enviando: {comando_restore}"
        )

        resposta_restore = enviar_pjl(
            sock,
            comando_restore,
            esperar_resposta=True,
        )

        print()
        print(
            "Resposta:"
        )

        print(
            limpar_resposta(
                resposta_restore
            )
            or "(sem resposta)"
        )

        # =================================================
        # 6. DINQUIRE FINAL
        # =================================================

        print()
        print("-" * 72)
        print("6. DINQUIRE FINAL")
        print("-" * 72)

        resposta, valor_final = dinquire(
            sock,
            "DENSITY",
        )

        print()
        print(
            "@PJL DINQUIRE DENSITY"
        )

        print(
            limpar_resposta(resposta)
            or "(sem resposta)"
        )

        print()
        print(
            f"Valor final: {valor_final}"
        )

        if valor_final == valor_original:

            print()
            print(
                "✓ RESTAURAÇÃO CONFIRMADA."
            )

        else:

            print()
            print(
                "⚠ RESTAURAÇÃO NÃO CONFIRMADA."
            )

    except Exception as erro:

        print()
        print("-" * 72)
        print("ERRO")
        print("-" * 72)

        print()
        print(
            f"{type(erro).__name__}: {erro}"
        )

    finally:

        # =================================================
        # ENCERRAMENTO
        # =================================================

        if sock is not None:

            try:
                # Fecha a sessão PJL.
                sock.sendall(
                    UNIVERSAL_RESET
                )
            except Exception:
                pass

            try:
                sock.close()
            except Exception:
                pass

        print()
        print("=" * 72)
        print("SESSÃO PJL ENCERRADA")
        print("=" * 72)
        print()


if __name__ == "__main__":
    testar()