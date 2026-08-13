"""
Printer Assistant - PJL Explicit Duplex Job Probe

Testa DUPLEX explicitamente dentro de um job PJL/PCL.

Este teste:
- não altera DEFAULT;
- testa DUPLEX=ON;
- testa DUPLEX=OFF;
- envia duas páginas por job;
- mantém cada job em uma única conexão RAW;
- possui tentativas de reconexão;
- não continua caso a conexão RAW não esteja disponível.

IMPORTANTE:
A confirmação física do duplex continua sendo necessária.
"""

import socket
import time


class PJLDuplexProbe:
    def __init__(
        self,
        ip,
        port=9100,
        timeout=5,
        retries=3,
        retry_delay=1.0,
    ):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def conectar(self):
        ultimo_erro = None

        for tentativa in range(1, self.retries + 1):
            sock = None

            try:
                print(
                    f"Conectando em "
                    f"{self.ip}:{self.port} "
                    f"(tentativa {tentativa}/{self.retries})..."
                )

                sock = socket.create_connection(
                    (self.ip, self.port),
                    timeout=self.timeout,
                )

                sock.settimeout(self.timeout)

                print("Conectado.")
                return sock

            except (OSError, TimeoutError) as exc:
                ultimo_erro = exc

                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

                if tentativa < self.retries:
                    print(
                        f"Falha na conexão: {exc}"
                    )
                    print(
                        f"Aguardando "
                        f"{self.retry_delay:.1f}s..."
                    )
                    time.sleep(self.retry_delay)

        raise ConnectionError(
            f"Não foi possível conectar em "
            f"{self.ip}:{self.port} "
            f"após {self.retries} tentativas. "
            f"Último erro: {ultimo_erro}"
        )

    def enviar_consulta(self, comando):
        sock = None

        try:
            sock = self.conectar()

            if not comando.endswith("\r\n"):
                comando += "\r\n"

            sock.sendall(
                comando.encode(
                    "ascii",
                    errors="replace",
                )
            )

            time.sleep(0.20)

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

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    def inquire(self, variavel):
        resposta = self.enviar_consulta(
            f"@PJL INQUIRE {variavel}"
        )

        return self.extrair_valor(
            resposta,
            variavel,
        )

    def dinquire(self, variavel):
        resposta = self.enviar_consulta(
            f"@PJL DINQUIRE {variavel}"
        )

        return self.extrair_valor(
            resposta,
            variavel,
        )

    @staticmethod
    def extrair_valor(resposta, variavel):
        if not resposta:
            return None

        alvo = variavel.strip().upper()

        for linha in resposta.splitlines():
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

    @staticmethod
    def gerar_pcl_pagina(numero):
        """
        Gera uma página PCL simples.

        Cada página possui conteúdo visual diferente
        para permitir identificação física.
        """

        texto = (
            f"PRINTER ASSISTANT - DUPLEX TEST\n"
            f"JOB PAGE {numero}\n"
        )

        comandos = bytearray()

        comandos.extend(
            b"\x1bE"
        )

        comandos.extend(
            b"\x1b&l0O"
        )

        comandos.extend(
            b"\x1b&l6D"
        )

        comandos.extend(
            b"\x1b&l8D"
        )

        comandos.extend(
            b"\x1b&l0E"
        )

        comandos.extend(
            b"\x1b&a0L"
        )

        comandos.extend(
            b"\x1b*p0x0Y"
        )

        comandos.extend(
            b"\x1b(s4099T"
        )

        comandos.extend(
            b"\x1b(s1p12v0s0b4099T"
        )

        comandos.extend(
            texto.encode(
                "cp858",
                errors="replace",
            )
        )

        comandos.extend(
            b"\x0c"
        )

        return bytes(comandos)

    def enviar_job(self, duplex):
        sock = None

        try:
            sock = self.conectar()

            inicio = time.monotonic()

            cabecalho = (
                "\x1b%-12345X"
                "@PJL JOB NAME=\"PA_DUPLEX_TEST\"\r\n"
                f"@PJL SET DUPLEX={duplex}\r\n"
                "@PJL ENTER LANGUAGE=PCL\r\n"
            )

            dados = bytearray()

            dados.extend(
                cabecalho.encode(
                    "ascii",
                    errors="replace",
                )
            )

            dados.extend(
                self.gerar_pcl_pagina(1)
            )

            dados.extend(
                self.gerar_pcl_pagina(2)
            )

            dados.extend(
                b"\x1b%-12345X"
            )

            dados.extend(
                b"@PJL EOJ\r\n"
            )

            dados.extend(
                b"\x1b%-12345X"
            )

            sock.sendall(bytes(dados))

            tempo = time.monotonic() - inicio

            return len(dados), tempo

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def imprimir_estado(probe):
    corrente = probe.inquire("DUPLEX")
    padrao = probe.dinquire("DUPLEX")

    print(
        f"INQUIRE  : {corrente}"
    )

    print(
        f"DINQUIRE : {padrao}"
    )

    return corrente, padrao


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL EXPLICIT DUPLEX JOB PROBE")
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

    print(
        "Este teste NÃO altera DEFAULT."
    )

    print()
    print(
        "Serão enviados dois jobs."
    )

    print()
    print("JOB A:")
    print("  @PJL SET DUPLEX=ON")
    print("  2 páginas dentro do MESMO job")

    print()
    print("JOB B:")
    print("  @PJL SET DUPLEX=OFF")
    print("  2 páginas dentro do MESMO job")

    print()
    print(
        "A impressora deverá imprimir "
        "quatro páginas no total."
    )

    print()
    print(
        "IMPORTANTE:"
    )
    print(
        "Se a conexão RAW estiver ocupada, "
        "o programa fará novas tentativas."
    )

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    probe = PJLDuplexProbe(
        ip=ip,
        port=9100,
        timeout=5,
        retries=3,
        retry_delay=1.0,
    )

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    try:
        original_corrente, original_default = (
            imprimir_estado(probe)
        )
    except Exception as exc:
        print()
        print("ERRO AO CONSULTAR A IMPRESSORA:")
        print(exc)
        return

    print()
    print("=" * 72)
    print("2. JOB A - DUPLEX=ON")
    print("=" * 72)

    print()
    print(
        "O job conterá:"
    )

    print()
    print(
        "@PJL SET DUPLEX=ON"
    )

    print(
        "@PJL ENTER LANGUAGE=PCL"
    )

    print()
    print(
        "PÁGINA 1"
    )

    print(
        "PÁGINA 2"
    )

    input(
        "\nPressione ENTER para enviar o JOB A..."
    )

    try:
        bytes_a, tempo_a = probe.enviar_job(
            "ON"
        )

        print()
        print(
            "JOB A enviado."
        )

        print(
            f"Bytes enviados: {bytes_a}"
        )

        print(
            f"Tempo:          {tempo_a:.3f}s"
        )

    except Exception as exc:
        print()
        print(
            "ERRO AO ENVIAR JOB A:"
        )
        print(exc)

        print()
        print(
            "O teste foi interrompido antes "
            "do JOB B."
        )

        return

    print()
    print(
        "Observe fisicamente:"
    )

    print(
        "- se houve impressão frente e verso;"
    )

    print(
        "- se o papel passou pelo caminho duplex;"
    )

    print(
        "- se o solenoide/mecanismo duplex foi acionado;"
    )

    print(
        "- se as duas páginas ficaram "
        "na mesma folha."
    )

    input(
        "\nPressione ENTER para continuar "
        "com o JOB B..."
    )

    print()
    print("=" * 72)
    print("3. JOB B - DUPLEX=OFF")
    print("=" * 72)

    print()
    print(
        "O job conterá:"
    )

    print()
    print(
        "@PJL SET DUPLEX=OFF"
    )

    print(
        "@PJL ENTER LANGUAGE=PCL"
    )

    print()
    print(
        "PÁGINA 1"
    )

    print(
        "PÁGINA 2"
    )

    input(
        "\nPressione ENTER para enviar o JOB B..."
    )

    try:
        bytes_b, tempo_b = probe.enviar_job(
            "OFF"
        )

        print()
        print(
            "JOB B enviado."
        )

        print(
            f"Bytes enviados: {bytes_b}"
        )

        print(
            f"Tempo:          {tempo_b:.3f}s"
        )

    except Exception as exc:
        print()
        print(
            "ERRO AO ENVIAR JOB B:"
        )
        print(exc)

        return

    print()
    print("=" * 72)
    print("4. ESTADO FINAL")
    print("=" * 72)

    try:
        final_corrente, final_default = (
            imprimir_estado(probe)
        )
    except Exception as exc:
        print()
        print(
            "ERRO AO consultar estado final:"
        )
        print(exc)
        return

    print()
    print(
        f"Corrente original : "
        f"{original_corrente}"
    )

    print(
        f"Default original  : "
        f"{original_default}"
    )

    print(
        f"Corrente final    : "
        f"{final_corrente}"
    )

    print(
        f"Default final     : "
        f"{final_default}"
    )

    if (
        str(final_corrente).upper()
        == str(original_corrente).upper()
        and
        str(final_default).upper()
        == str(original_default).upper()
    ):
        print()
        print(
            "✓ ESTADO PJL RESTAURADO."
        )
    else:
        print()
        print(
            "⚠ O ESTADO FINAL É DIFERENTE "
            "DO ESTADO ORIGINAL."
        )

    print()
    print("=" * 72)
    print("RESULTADO FÍSICO")
    print("=" * 72)

    print()
    print(
        "JOB A = DUPLEX=ON"
    )

    print(
        "JOB B = DUPLEX=OFF"
    )

    print()
    print(
        "Compare fisicamente os quatro lados "
        "impressos."
    )

    print()
    print(
        "Nenhum DEFAULT foi alterado."
    )

    print()


if __name__ == "__main__":
    main()