import socket
import time


HOST_PORT = 9100
CONNECT_TIMEOUT = 3.0
RECV_TIMEOUT = 2.0
MAX_RETRIES = 3


def conectar(ip):
    ultimo_erro = None

    for tentativa in range(1, MAX_RETRIES + 1):
        print(
            f"Conectando em {ip}:{HOST_PORT} "
            f"(tentativa {tentativa}/{MAX_RETRIES})..."
        )

        try:
            sock = socket.create_connection(
                (ip, HOST_PORT),
                timeout=CONNECT_TIMEOUT,
            )
            sock.settimeout(RECV_TIMEOUT)
            print("Conectado.")
            return sock

        except (socket.timeout, OSError) as erro:
            ultimo_erro = erro

            if tentativa < MAX_RETRIES:
                time.sleep(0.5)

    raise ConnectionError(
        f"Não foi possível conectar em {ip}:{HOST_PORT}: {ultimo_erro}"
    )


def enviar_pjl(ip, comando, aguardar_resposta=True):
    inicio = time.perf_counter()

    sock = conectar(ip)

    try:
        payload = (comando.rstrip("\r\n") + "\r\n").encode("ascii")

        sock.sendall(payload)

        if not aguardar_resposta:
            return "", time.perf_counter() - inicio

        dados = bytearray()

        while True:
            try:
                bloco = sock.recv(4096)

                if not bloco:
                    break

                dados.extend(bloco)

                if b"\x0c" in bloco:
                    break

            except socket.timeout:
                break

        resposta = bytes(dados).decode(
            "latin-1",
            errors="replace",
        )

        return resposta, time.perf_counter() - inicio

    finally:
        sock.close()


def limpar_resposta(resposta):
    if not resposta:
        return None

    texto = resposta.replace("\x00", "").strip()

    if not texto:
        return None

    linhas = []

    for linha in texto.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        if linha.startswith("@PJL"):
            continue

        linhas.append(linha)

    if not linhas:
        return texto

    return "\n".join(linhas).strip()


def inquire(ip, variavel):
    comando = f"@PJL INQUIRE {variavel}"

    resposta, tempo = enviar_pjl(
        ip,
        comando,
        aguardar_resposta=True,
    )

    valor = limpar_resposta(resposta)

    return valor, tempo


def dinquire(ip, variavel):
    comando = f"@PJL DINQUIRE {variavel}"

    resposta, tempo = enviar_pjl(
        ip,
        comando,
        aguardar_resposta=True,
    )

    valor = limpar_resposta(resposta)

    return valor, tempo


def info_job(ip):
    comando = "@PJL INFO STATUS"

    resposta, tempo = enviar_pjl(
        ip,
        comando,
        aguardar_resposta=True,
    )

    return limpar_resposta(resposta), tempo


def info_config(ip):
    comando = "@PJL INFO CONFIG"

    resposta, tempo = enviar_pjl(
        ip,
        comando,
        aguardar_resposta=True,
    )

    return limpar_resposta(resposta), tempo


def mostrar_consulta(ip, variavel):
    print(f"\n## VARIÁVEL: {variavel}")
    print()

    valor_inquire, tempo_inquire = inquire(
        ip,
        variavel,
    )

    print(f"INQUIRE  : {valor_inquire}")
    print(f"Tempo    : {tempo_inquire:.3f}s")

    valor_dinquire, tempo_dinquire = dinquire(
        ip,
        variavel,
    )

    print(f"DINQUIRE : {valor_dinquire}")
    print(f"Tempo    : {tempo_dinquire:.3f}s")

    return {
        "variable": variavel,
        "inquire": valor_inquire,
        "dinquire": valor_dinquire,
        "inquire_time": tempo_inquire,
        "dinquire_time": tempo_dinquire,
    }


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 JOB CONTROL PROBE")
    print("=" * 72)

    ip = input("Digite o IP da impressora: ").strip()

    if not ip:
        print("IP inválido.")
        return

    print()
    print(f"Impressora: {ip}")
    print(f"RAW:        {HOST_PORT}")
    print()

    print("Este teste:")
    print()
    print("- NÃO executa SET.")
    print("- NÃO executa DEFAULT.")
    print("- NÃO executa RESET.")
    print("- NÃO envia jobs.")
    print("- NÃO imprime nenhuma página.")
    print("- NÃO altera configurações.")
    print()
    print("Serão somente consultadas informações relacionadas")
    print("ao controle e identificação de jobs.")
    print()

    continuar = input("Continuar? [S/N]: ").strip().upper()

    if continuar != "S":
        print("Teste cancelado.")
        return

    print()
    print("=" * 72)
    print("1. IDENTIDADE / CONFIGURAÇÃO")
    print("=" * 72)

    try:
        resposta_id, tempo_id = enviar_pjl(
            ip,
            "@PJL INFO ID",
            aguardar_resposta=True,
        )

        print()
        print("@PJL INFO ID")
        print(limpar_resposta(resposta_id))
        print(f"Tempo: {tempo_id:.3f}s")

    except Exception as erro:
        print()
        print(f"ERRO INFO ID: {erro}")

    try:
        resposta_config, tempo_config = info_config(ip)

        print()
        print("@PJL INFO CONFIG")
        print("-" * 72)

        if resposta_config:
            print(resposta_config)
        else:
            print("(sem resposta)")

        print("-" * 72)
        print(f"Tempo: {tempo_config:.3f}s")

    except Exception as erro:
        print()
        print(f"ERRO INFO CONFIG: {erro}")

    print()
    print("=" * 72)
    print("2. CONSULTAS DE CONTROLE DE JOB")
    print("=" * 72)

    variaveis = [
        "JOBNAME",
        "USERNAME",
        "USTATUS",
        "JOBID",
        "JOBNAME",
        "JOBSTATUS",
        "JOBINFO",
        "PAGECOUNT",
        "PAGENUM",
        "PAGES",
        "COPIES",
        "DUPLEX",
        "ORIENTATION",
        "RESOLUTION",
        "DENSITY",
        "PAPER",
        "MEDIATYPE",
        "MEDIASOURCE",
        "TRAY",
        "INPUTTRAY",
        "OUTPUTBIN",
    ]

    resultados = []

    for variavel in variaveis:
        print()
        print("-" * 72)

        try:
            resultado = mostrar_consulta(
                ip,
                variavel,
            )

            resultados.append(resultado)

        except Exception as erro:
            print(f"ERRO ao consultar {variavel}: {erro}")

            resultados.append(
                {
                    "variable": variavel,
                    "inquire": None,
                    "dinquire": None,
                    "error": str(erro),
                }
            )

    print()
    print("=" * 72)
    print("3. RESUMO")
    print("=" * 72)

    print()

    print(
        f"{'VARIÁVEL':<16}"
        f"{'INQUIRE':<24}"
        f"{'DINQUIRE':<24}"
    )

    print("-" * 64)

    for resultado in resultados:
        variavel = resultado["variable"]

        inquire_valor = resultado.get(
            "inquire",
            None,
        )

        dinquire_valor = resultado.get(
            "dinquire",
            None,
        )

        print(
            f"{variavel:<16}"
            f"{str(inquire_valor):<24}"
            f"{str(dinquire_valor):<24}"
        )

    print()
    print("=" * 72)
    print("4. INTERPRETAÇÃO")
    print("=" * 72)
    print()

    print("Variáveis que retornaram valor:")
    print()

    encontrou = False

    for resultado in resultados:
        inquire_valor = resultado.get("inquire")
        dinquire_valor = resultado.get("dinquire")

        if (
            inquire_valor is not None
            and inquire_valor != '"?"'
        ) or (
            dinquire_valor is not None
            and dinquire_valor != '"?"'
        ):
            encontrou = True

            print(
                f"- {resultado['variable']}: "
                f"INQUIRE={inquire_valor} | "
                f"DINQUIRE={dinquire_valor}"
            )

    if not encontrou:
        print("(nenhuma variável retornou valor útil)")

    print()
    print("Variáveis que responderam \"?\" ou não responderam")
    print("não serão consideradas suportadas apenas por essa consulta.")
    print()
    print("O próximo estágio deverá testar somente as variáveis")
    print("que demonstrarem comportamento consistente.")
    print()
    print("Nenhuma configuração foi alterada.")
    print("Nenhum DEFAULT foi alterado.")
    print("Nenhum SET foi executado.")
    print("Nenhum RESET foi executado.")
    print("Nenhum job foi enviado.")
    print()
    print("Conexão RAW encerrada.")


if __name__ == "__main__":
    main()