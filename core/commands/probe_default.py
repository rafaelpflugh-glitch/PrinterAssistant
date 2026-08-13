"""
Printer Assistant - PJL DEFAULT Probe

Investiga a diferença entre:

    @PJL SET
    @PJL DEFAULT
    @PJL INQUIRE
    @PJL DINQUIRE

O teste usa DENSITY como variável controlada.

Objetivos:

1. Descobrir o valor corrente com INQUIRE.
2. Descobrir o valor default com DINQUIRE.
3. Executar SET DENSITY=4.
4. Verificar INQUIRE e DINQUIRE.
5. Executar DEFAULT DENSITY=4.
6. Verificar novamente INQUIRE e DINQUIRE.
7. Restaurar DEFAULT DENSITY=3.
8. Confirmar o estado final.

IMPORTANTE:

- O teste não assume previamente que DINQUIRE muda após SET.
- SET e DEFAULT são tratados como operações diferentes.
- A conexão RAW permanece aberta durante toda a sequência.
- O teste tenta restaurar o default original ao final.
"""

import socket
import time


HOST = "192.168.14.134"
PORT = 9100

TEST_VALUE = "4"
RESTORE_VALUE = "3"

TIMEOUT = 5
WAIT_AFTER_COMMAND = 1.0


def abrir_conexao(host, port):
    """
    Abre uma conexão RAW com a impressora.
    """

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    sock.settimeout(TIMEOUT)

    print()
    print("Abrindo conexão RAW...")
    print(f"Conectando em {host}:{port}")

    sock.connect((host, port))

    print("Conectado.")

    return sock


def enviar(sock, comando, esperar=WAIT_AFTER_COMMAND):
    """
    Envia um comando PJL pela conexão existente.

    Retorna todos os bytes recebidos após o comando.
    """

    if not comando.endswith("\r\n"):
        comando += "\r\n"

    print()
    print(f"Enviando:")
    print(comando.rstrip())

    sock.sendall(
        comando.encode(
            "ascii",
            errors="replace",
        )
    )

    time.sleep(esperar)

    resposta = b""

    while True:

        try:
            bloco = sock.recv(4096)

        except socket.timeout:
            break

        if not bloco:
            break

        resposta += bloco

        if len(bloco) < 4096:
            break

    return resposta


def limpar_resposta(resposta):
    """
    Converte a resposta da impressora para texto legível.
    """

    if not resposta:
        return "(sem resposta)"

    texto = resposta.decode(
        "latin-1",
        errors="replace",
    )

    return texto.strip()


def consultar_inquire(sock, variavel):
    """
    Executa:

        @PJL INQUIRE VAR

    Retorna o valor observado no ambiente corrente.
    """

    resposta = enviar(
        sock,
        f"@PJL INQUIRE {variavel}",
    )

    texto = limpar_resposta(resposta)

    print()
    print(f"Resposta INQUIRE {variavel}:")
    print(texto)

    return texto


def consultar_dinquire(sock, variavel):
    """
    Executa:

        @PJL DINQUIRE VAR

    Retorna o valor default observado.
    """

    resposta = enviar(
        sock,
        f"@PJL DINQUIRE {variavel}",
    )

    texto = limpar_resposta(resposta)

    print()
    print(f"Resposta DINQUIRE {variavel}:")
    print(texto)

    return texto


def extrair_valor_simples(texto):
    """
    Extrai o último valor útil de uma resposta PJL simples.

    Exemplo:

        @PJL INQUIRE DENSITY
        3

    retorna:

        3
    """

    if not texto:
        return None

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    if not linhas:
        return None

    for linha in reversed(linhas):

        if linha.startswith("@PJL"):
            continue

        return linha.strip().strip('"')

    return None


def separador(titulo):
    """
    Imprime uma seção visual no terminal.
    """

    print()
    print("=" * 72)
    print(titulo)
    print("=" * 72)


def main():
    """
    Executa o teste completo.
    """

    separador(
        "PRINTER ASSISTANT - PJL DEFAULT PROBE"
    )

    print()
    print(f"Impressora: {HOST}")
    print(f"RAW:        {HOST}:{PORT}")

    print()
    print("Variável controlada : DENSITY")
    print(f"Valor de teste      : {TEST_VALUE}")
    print(f"Valor de restauração: {RESTORE_VALUE}")

    print()
    print("Este teste investigará:")
    print()
    print("  SET     -> ambiente corrente")
    print("  DEFAULT -> configuração default")
    print("  INQUIRE -> valor corrente")
    print("  DINQUIRE -> valor default")
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print()
        print("Teste cancelado.")
        return

    sock = None

    original_default = None
    original_current = None

    try:

        sock = abrir_conexao(
            HOST,
            PORT,
        )

        # ==================================================
        # 1. ESTADO INICIAL
        # ==================================================

        separador(
            "1. ESTADO INICIAL"
        )

        print()
        print("Consultando DINQUIRE DENSITY...")

        resposta_default = consultar_dinquire(
            sock,
            "DENSITY",
        )

        original_default = extrair_valor_simples(
            resposta_default
        )

        print()
        print(
            f"DEFAULT DESCOBERTO: "
            f"{original_default}"
        )

        print()
        print("Consultando INQUIRE DENSITY...")

        resposta_current = consultar_inquire(
            sock,
            "DENSITY",
        )

        original_current = extrair_valor_simples(
            resposta_current
        )

        print()
        print(
            f"VALOR CORRENTE DESCOBERTO: "
            f"{original_current}"
        )

        # ==================================================
        # 2. SET
        # ==================================================

        separador(
            "2. TESTE SET"
        )

        print()
        print(
            f"Executando SET DENSITY={TEST_VALUE}"
        )

        resposta = enviar(
            sock,
            f"@PJL SET DENSITY={TEST_VALUE}",
        )

        print()
        print("Resposta:")
        print(limpar_resposta(resposta))

        # ==================================================
        # 3. CONSULTAS APÓS SET
        # ==================================================

        separador(
            "3. CONSULTAS APÓS SET"
        )

        print()
        print("INQUIRE DENSITY:")

        inquire_after_set = consultar_inquire(
            sock,
            "DENSITY",
        )

        current_after_set = extrair_valor_simples(
            inquire_after_set
        )

        print()
        print(
            f"Valor corrente após SET: "
            f"{current_after_set}"
        )

        print()
        print("DINQUIRE DENSITY:")

        dinquire_after_set = consultar_dinquire(
            sock,
            "DENSITY",
        )

        default_after_set = extrair_valor_simples(
            dinquire_after_set
        )

        print()
        print(
            f"Valor default após SET: "
            f"{default_after_set}"
        )

        # ==================================================
        # 4. DEFAULT
        # ==================================================

        separador(
            "4. TESTE DEFAULT"
        )

        print()
        print(
            f"Executando DEFAULT DENSITY={TEST_VALUE}"
        )

        resposta = enviar(
            sock,
            f"@PJL DEFAULT DENSITY={TEST_VALUE}",
        )

        print()
        print("Resposta:")
        print(limpar_resposta(resposta))

        # ==================================================
        # 5. CONSULTAS APÓS DEFAULT
        # ==================================================

        separador(
            "5. CONSULTAS APÓS DEFAULT"
        )

        print()
        print("INQUIRE DENSITY:")

        inquire_after_default = consultar_inquire(
            sock,
            "DENSITY",
        )

        current_after_default = extrair_valor_simples(
            inquire_after_default
        )

        print()
        print(
            f"Valor corrente após DEFAULT: "
            f"{current_after_default}"
        )

        print()
        print("DINQUIRE DENSITY:")

        dinquire_after_default = consultar_dinquire(
            sock,
            "DENSITY",
        )

        default_after_default = extrair_valor_simples(
            dinquire_after_default
        )

        print()
        print(
            f"Valor default após DEFAULT: "
            f"{default_after_default}"
        )

        # ==================================================
        # 6. TESTE DE IDIOMA
        # ==================================================

        separador(
            "6. TESTE CONTROLADO DE IDIOMA"
        )

        print()
        print(
            "A variável LANG declarou explicitamente "
            "ENGLISH como valor válido."
        )

        print()
        print(
            "Neste probe NÃO vamos alterar LANG ainda."
        )

        print(
            "Primeiro precisamos confirmar que "
            "DEFAULT funciona de forma persistente."
        )

        # ==================================================
        # 7. RESTAURAÇÃO
        # ==================================================

        separador(
            "7. RESTAURAÇÃO DO DEFAULT"
        )

        valor_restauracao = (
            original_default
            if original_default is not None
            else RESTORE_VALUE
        )

        print()
        print(
            f"Restaurando DEFAULT DENSITY="
            f"{valor_restauracao}"
        )

        resposta = enviar(
            sock,
            f"@PJL DEFAULT DENSITY="
            f"{valor_restauracao}",
        )

        print()
        print("Resposta:")
        print(limpar_resposta(resposta))

        # ==================================================
        # 8. VERIFICAÇÃO FINAL
        # ==================================================

        separador(
            "8. VERIFICAÇÃO FINAL"
        )

        print()
        print("INQUIRE DENSITY:")

        final_current_response = consultar_inquire(
            sock,
            "DENSITY",
        )

        final_current = extrair_valor_simples(
            final_current_response
        )

        print()
        print(
            f"Valor corrente final: "
            f"{final_current}"
        )

        print()
        print("DINQUIRE DENSITY:")

        final_default_response = consultar_dinquire(
            sock,
            "DENSITY",
        )

        final_default = extrair_valor_simples(
            final_default_response
        )

        print()
        print(
            f"Valor default final: "
            f"{final_default}"
        )

        # ==================================================
        # 9. RESUMO
        # ==================================================

        separador(
            "9. RESUMO DO EXPERIMENTO"
        )

        print()
        print(
            f"Inicial DINQUIRE : "
            f"{original_default}"
        )

        print(
            f"Inicial INQUIRE  : "
            f"{original_current}"
        )

        print()

        print(
            f"Após SET INQUIRE : "
            f"{current_after_set}"
        )

        print(
            f"Após SET DINQUIRE: "
            f"{default_after_set}"
        )

        print()

        print(
            f"Após DEFAULT INQUIRE : "
            f"{current_after_default}"
        )

        print(
            f"Após DEFAULT DINQUIRE: "
            f"{default_after_default}"
        )

        print()

        print(
            f"Final INQUIRE : "
            f"{final_current}"
        )

        print(
            f"Final DINQUIRE: "
            f"{final_default}"
        )

        print()

        if default_after_default == TEST_VALUE:

            print(
                "✓ DEFAULT ALTEROU O VALOR DEFAULT."
            )

        else:

            print(
                "⚠ DEFAULT NÃO ALTEROU O VALOR "
                "OBSERVADO POR DINQUIRE."
            )

        if current_after_default == TEST_VALUE:

            print(
                "✓ INQUIRE REFLETIU O NOVO DEFAULT."
            )

        else:

            print(
                "⚠ INQUIRE NÃO REFLETIU O DEFAULT."
            )

        if final_default == original_default:

            print(
                "✓ DEFAULT RESTAURADO."
            )

        else:

            print(
                "⚠ DEFAULT FINAL DIFERE DO ORIGINAL."
            )

        print()

    except ConnectionRefusedError:

        print()
        print(
            "ERRO: conexão recusada pela impressora."
        )

    except socket.timeout:

        print()
        print(
            "ERRO: timeout durante comunicação RAW."
        )

    except OSError as erro:

        print()
        print(
            f"ERRO DE REDE: {erro}"
        )

    finally:

        if sock is not None:

            try:
                sock.close()
            except OSError:
                pass

        print()
        print(
            "Conexão RAW encerrada."
        )

        print()
        print("=" * 72)


if __name__ == "__main__":
    main()