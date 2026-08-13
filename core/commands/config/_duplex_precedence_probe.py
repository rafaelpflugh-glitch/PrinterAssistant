"""
Printer Assistant - PJL/PCL Duplex Precedence Probe

Investiga a precedência entre:

    PJL SET DUPLEX
    PCL DUPLEX

Este teste NÃO altera DEFAULT.

Serão enviados quatro jobs, cada um contendo duas páginas:

JOB A:
    PJL SET DUPLEX=ON
    PCL SIMPLEX

JOB B:
    PJL SET DUPLEX=OFF
    PCL SIMPLEX

JOB C:
    PJL SET DUPLEX=ON
    PCL LONG EDGE

JOB D:
    PJL SET DUPLEX=OFF
    PCL SHORT EDGE

Objetivo:

Descobrir qual camada determina o comportamento físico
quando PJL e PCL possuem configurações conflitantes.
"""

import socket
import time


class DuplexPrecedenceProbe:
    def __init__(self, ip, port=9100, timeout=5, retries=3):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.retries = retries

    def conectar(self):
        ultimo_erro = None

        for tentativa in range(1, self.retries + 1):
            print(
                f"Conectando em {self.ip}:{self.port} "
                f"(tentativa {tentativa}/{self.retries})..."
            )

            try:
                sock = socket.create_connection(
                    (self.ip, self.port),
                    timeout=self.timeout,
                )

                sock.settimeout(self.timeout)

                print("Conectado.")

                return sock

            except Exception as exc:
                ultimo_erro = exc

                print(
                    f"Falha na conexão: {exc}"
                )

                if tentativa < self.retries:
                    time.sleep(0.5)

        raise ultimo_erro

    def enviar_pjl(self, comando):
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

            time.sleep(0.2)

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
        resposta = self.enviar_pjl(
            f"@PJL INQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def dinquire(self, variavel):
        resposta = self.enviar_pjl(
            f"@PJL DINQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    @staticmethod
    def extrair_valor(resposta):
        if not resposta:
            return None

        linhas = [
            linha.strip()
            for linha in resposta.splitlines()
            if linha.strip()
        ]

        if not linhas:
            return None

        for linha in linhas:
            if line_is_pjl_response(linha):
                continue

            return linha

        return None

    def enviar_job(self, nome, pjl_duplex, pcl_duplex):
        """
        Envia um job PCL de duas páginas.

        pcl_duplex:
            0 = simplex
            1 = long edge
            2 = short edge
        """

        if pcl_duplex == 0:
            descricao_pcl = "SIMPLEX"
        elif pcl_duplex == 1:
            descricao_pcl = "LONG EDGE"
        elif pcl_duplex == 2:
            descricao_pcl = "SHORT EDGE"
        else:
            raise ValueError(
                "Modo PCL duplex inválido."
            )

        print()
        print("=" * 72)
        print(nome)
        print("=" * 72)

        print(
            f"PJL DUPLEX : {pjl_duplex}"
        )

        print(
            f"PCL DUPLEX : {descricao_pcl}"
        )

        print()
        print(
            "O job possui duas páginas."
        )

        print(
            "Pressione ENTER para enviar..."
        )

        input()

        partes = []

        partes.append(
            "\x1b%-12345X"
        )

        partes.append(
            "@PJL JOB NAME=\"DUPLEX_PRECEDENCE\"\r\n"
        )

        partes.append(
            f"@PJL SET DUPLEX={pjl_duplex}\r\n"
        )

        partes.append(
            "@PJL ENTER LANGUAGE=PCL\r\n"
        )

        partes.append(
            "\x1bE"
        )

        # PCL duplex:
        #
        # 0 = simplex
        # 1 = long edge
        # 2 = short edge
        partes.append(
            f"\x1b&l{pcl_duplex}S"
        )

        partes.append(
            "\x1b&l6D"
        )

        partes.append(
            "\x1b&a0L"
        )

        partes.append(
            "\x1b&a0M"
        )

        partes.append(
            "\x1b&l0E"
        )

        partes.append(
            "\x1b&l0F"
        )

        # Página 1
        partes.append(
            "\x1b&a100H"
        )

        partes.append(
            "\x1b&a500V"
        )

        partes.append(
            f"{nome} - PAGINA 1\r\n"
        )

        partes.append(
            "\x0c"
        )

        # Página 2
        partes.append(
            "\x1b&a100H"
        )

        partes.append(
            "\x1b&a500V"
        )

        partes.append(
            f"{nome} - PAGINA 2\r\n"
        )

        partes.append(
            "\x0c"
        )

        partes.append(
            "\x1b%-12345X"
        )

        dados = "".join(partes).encode(
            "latin-1",
            errors="replace",
        )

        sock = None

        inicio = time.monotonic()

        try:
            sock = self.conectar()

            sock.sendall(dados)

            tempo = time.monotonic() - inicio

            print()
            print(
                f"{nome} enviado."
            )

            print(
                f"Bytes enviados: {len(dados)}"
            )

            print(
                f"Tempo:          {tempo:.3f}s"
            )

            return len(dados), tempo

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    def reset(self):
        print()
        print(
            "Enviando @PJL RESET..."
        )

        self.enviar_pjl(
            "@PJL RESET"
        )

        time.sleep(0.5)


def line_is_pjl_response(linha):
    upper = linha.upper()

    if upper.startswith("@PJL"):
        return True

    if upper.startswith("INQUIRE"):
        return True

    if upper.startswith("DINQUIRE"):
        return True

    return False


def main():
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - PJL/PCL DUPLEX PRECEDENCE PROBE"
    )
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    probe = DuplexPrecedenceProbe(
        ip=ip,
        port=9100,
        timeout=5,
        retries=3,
    )

    print()
    print(
        f"Impressora: {ip}"
    )

    print(
        "RAW:        9100"
    )

    print()
    print(
        "Este teste NÃO altera DEFAULT."
    )

    print()
    print(
        "Serão enviados quatro jobs:"
    )

    print()
    print(
        "JOB A"
    )
    print(
        "PJL SET DUPLEX=ON"
    )
    print(
        "PCL SIMPLEX"
    )

    print()
    print(
        "JOB B"
    )
    print(
        "PJL SET DUPLEX=OFF"
    )
    print(
        "PCL SIMPLEX"
    )

    print()
    print(
        "JOB C"
    )
    print(
        "PJL SET DUPLEX=ON"
    )
    print(
        "PCL LONG EDGE"
    )

    print()
    print(
        "JOB D"
    )
    print(
        "PJL SET DUPLEX=OFF"
    )
    print(
        "PCL SHORT EDGE"
    )

    print()
    print(
        "Cada job possui duas páginas."
    )

    print(
        "Total esperado: oito páginas."
    )

    print()
    print(
        "Continuar? [S/N]: "
    )

    confirmar = input().strip().upper()

    if confirmar != "S":
        print(
            "Teste cancelado."
        )
        return

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    corrente_original = probe.inquire(
        "DUPLEX"
    )

    default_original = probe.dinquire(
        "DUPLEX"
    )

    print(
        f"INQUIRE  : {corrente_original}"
    )

    print(
        f"DINQUIRE : {default_original}"
    )

    resultados = []

    resultados.append(
        probe.enviar_job(
            "JOB A",
            "ON",
            0,
        )
    )

    probe.reset()

    resultados.append(
        probe.enviar_job(
            "JOB B",
            "OFF",
            0,
        )
    )

    probe.reset()

    resultados.append(
        probe.enviar_job(
            "JOB C",
            "ON",
            1,
        )
    )

    probe.reset()

    resultados.append(
        probe.enviar_job(
            "JOB D",
            "OFF",
            2,
        )
    )

    probe.reset()

    print()
    print("=" * 72)
    print("2. ESTADO FINAL")
    print("=" * 72)

    corrente_final = probe.inquire(
        "DUPLEX"
    )

    default_final = probe.dinquire(
        "DUPLEX"
    )

    print(
        f"INQUIRE  : {corrente_final}"
    )

    print(
        f"DINQUIRE : {default_final}"
    )

    print()
    print(
        f"Corrente original : {corrente_original}"
    )

    print(
        f"Corrente final    : {corrente_final}"
    )

    print(
        f"Default original  : {default_original}"
    )

    print(
        f"Default final     : {default_final}"
    )

    if (
        corrente_final == corrente_original
        and default_final == default_original
    ):
        print()
        print(
            "✓ ESTADO PJL RESTAURADO."
        )
    else:
        print()
        print(
            "✗ ESTADO FINAL DIFERE DO ORIGINAL."
        )

    print()
    print("=" * 72)
    print("3. MATRIZ DE PRECEDÊNCIA")
    print("=" * 72)

    print()
    print(
        "JOB A:"
    )
    print(
        "PJL ON + PCL SIMPLEX"
    )

    print(
        "Observe se imprime:"
    )

    print(
        "  simplex ou duplex"
    )

    print()
    print(
        "JOB B:"
    )
    print(
        "PJL OFF + PCL SIMPLEX"
    )

    print(
        "Observe se imprime:"
    )

    print(
        "  simplex ou duplex"
    )

    print()
    print(
        "JOB C:"
    )
    print(
        "PJL ON + PCL LONG EDGE"
    )

    print(
        "Observe se imprime:"
    )

    print(
        "  simplex ou duplex"
    )

    print()
    print(
        "JOB D:"
    )

    print(
        "PJL OFF + PCL SHORT EDGE"
    )

    print(
        "Observe se imprime:"
    )

    print(
        "  simplex ou duplex"
    )

    print()
    print(
        "RESULTADOS DOS JOBS:"
    )

    for indice, resultado in enumerate(
        resultados,
        start=1,
    ):
        bytes_enviados, tempo = resultado

        print(
            f"JOB {indice}: "
            f"{bytes_enviados} bytes / "
            f"{tempo:.3f}s"
        )

    print()
    print(
        "Nenhum DEFAULT foi alterado."
    )


if __name__ == "__main__":
    main()