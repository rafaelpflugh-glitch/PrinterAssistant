"""
Printer Assistant - PJL/PCL Duplex Matrix Probe

Investiga como a impressora Lexmark MX611DHE aplica duplex
durante um job de impressão.

Este teste NÃO altera DEFAULT.

São realizados três jobs independentes:

JOB A
    PJL SET DUPLEX=ON
    PCL sem comando explícito de duplex

JOB B
    PJL SET DUPLEX=OFF
    PCL DUPLEX explícito através de:
        ESC & l 1 S

JOB C
    PJL SET DUPLEX=ON
    PCL DUPLEX explícito através de:
        ESC & l 1 S

Cada job possui duas páginas.

Objetivo:
    descobrir se o duplex é controlado por:
        - ambiente PJL;
        - comando PCL;
        - combinação PJL + PCL.

Nenhum DEFAULT é alterado.
"""


import socket
import time


ESC = b"\x1b"
UEL = b"\x1b%-12345X"


class DuplexMatrixProbe:
    def __init__(self, ip, port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    # ==========================================================
    # CONEXÃO
    # ==========================================================

    def conectar(self, tentativas=3):
        ultimo_erro = None

        for tentativa in range(1, tentativas + 1):
            sock = None

            try:
                print(
                    f"Conectando em "
                    f"{self.ip}:{self.port} "
                    f"(tentativa {tentativa}/{tentativas})..."
                )

                sock = socket.create_connection(
                    (self.ip, self.port),
                    timeout=self.timeout,
                )

                sock.settimeout(self.timeout)

                print("Conectado.")

                return sock

            except OSError as exc:
                ultimo_erro = exc

                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

                if tentativa < tentativas:
                    time.sleep(1)

        raise ConnectionError(
            f"Não foi possível conectar em "
            f"{self.ip}:{self.port}: {ultimo_erro}"
        )

    # ==========================================================
    # CONSULTA PJL
    # ==========================================================

    def consultar(self, comando):
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

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    def inquire(self, variavel):
        resposta = self.consultar(
            f"@PJL INQUIRE {variavel}"
        )

        return self.extrair_valor(
            resposta,
            variavel,
        )

    def dinquire(self, variavel):
        resposta = self.consultar(
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
                nome, valor = linha.split("=", 1)

                if nome.strip().upper() == alvo:
                    return valor.strip().strip('"')

            return linha.strip('"')

        return None

    # ==========================================================
    # SET PJL
    # ==========================================================

    def set_variavel(self, variavel, valor):
        comando = f"@PJL SET {variavel}={valor}"

        print()
        print(f"Enviando: {comando}")

        resposta = self.consultar(comando)

        if resposta:
            print("Resposta:")
            print(resposta)
        else:
            print("(sem resposta PJL)")

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        print()
        print("Enviando:")
        print("@PJL RESET")

        resposta = self.consultar(
            "@PJL RESET"
        )

        if resposta:
            print("Resposta:")
            print(resposta)
        else:
            print("(sem resposta PJL)")

    # ==========================================================
    # JOB PCL
    # ==========================================================

    def construir_job(
        self,
        numero,
        duplex_pjl,
        duplex_pcl=False,
    ):
        partes = []

        # ------------------------------------------------------
        # UEL inicial
        # ------------------------------------------------------

        partes.append(UEL)

        # ------------------------------------------------------
        # PJL JOB
        # ------------------------------------------------------

        partes.append(
            (
                f"@PJL JOB NAME=\"DUPLEX_MATRIX_{numero}\"\r\n"
            ).encode("ascii")
        )

        # ------------------------------------------------------
        # PJL DUPLEX
        # ------------------------------------------------------

        partes.append(
            (
                f"@PJL SET DUPLEX={duplex_pjl}\r\n"
            ).encode("ascii")
        )

        # ------------------------------------------------------
        # Entrada em PCL
        # ------------------------------------------------------

        partes.append(
            b"@PJL ENTER LANGUAGE=PCL\r\n"
        )

        # ------------------------------------------------------
        # PCL reset
        # ------------------------------------------------------

        partes.append(
            ESC + b"E"
        )

        # ------------------------------------------------------
        # Duplex PCL opcional
        #
        # ESC & l 1 S
        #
        # 0 = simplex
        # 1 = duplex long edge
        # 2 = duplex short edge
        # ------------------------------------------------------

        if duplex_pcl:
            partes.append(
                ESC + b"&l1S"
            )

        # ------------------------------------------------------
        # Orientação PCL
        #
        # 0 = portrait
        # 1 = landscape
        # ------------------------------------------------------

        partes.append(
            ESC + b"&l0O"
        )

        # ------------------------------------------------------
        # Página 1
        # ------------------------------------------------------

        texto1 = (
            f"PRINTER ASSISTANT\r\n"
            f"DUPLEX MATRIX - JOB {numero}\r\n"
            f"PAGE 1\r\n"
            f"PJL={duplex_pjl}\r\n"
            f"PCL_DUPLEX={duplex_pcl}\r\n"
        )

        partes.append(
            ESC + b"&l6D"
        )

        partes.append(
            texto1.encode(
                "cp850",
                errors="replace",
            )
        )

        # Form feed
        partes.append(
            b"\x0c"
        )

        # ------------------------------------------------------
        # Página 2
        # ------------------------------------------------------

        texto2 = (
            f"PRINTER ASSISTANT\r\n"
            f"DUPLEX MATRIX - JOB {numero}\r\n"
            f"PAGE 2\r\n"
            f"PJL={duplex_pjl}\r\n"
            f"PCL_DUPLEX={duplex_pcl}\r\n"
        )

        partes.append(
            texto2.encode(
                "cp850",
                errors="replace",
            )
        )

        # Finaliza página
        partes.append(
            b"\x0c"
        )

        # ------------------------------------------------------
        # Sai do PCL
        # ------------------------------------------------------

        partes.append(
            UEL
        )

        # ------------------------------------------------------
        # Fim do job
        # ------------------------------------------------------

        partes.append(
            b"@PJL EOJ\r\n"
        )

        partes.append(
            UEL
        )

        return b"".join(partes)

    # ==========================================================
    # ENVIO
    # ==========================================================

    def enviar_job(
        self,
        numero,
        duplex_pjl,
        duplex_pcl,
    ):
        dados = self.construir_job(
            numero=numero,
            duplex_pjl=duplex_pjl,
            duplex_pcl=duplex_pcl,
        )

        sock = None

        try:
            sock = self.conectar()

            inicio = time.monotonic()

            sock.sendall(dados)

            tempo = time.monotonic() - inicio

            return len(dados), tempo

        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


def mostrar_estado(probe, titulo):
    print()
    print("=" * 72)
    print(titulo)
    print("=" * 72)

    corrente = probe.inquire("DUPLEX")
    padrao = probe.dinquire("DUPLEX")

    print(f"INQUIRE  : {corrente}")
    print(f"DINQUIRE : {padrao}")

    return corrente, padrao


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL/PCL DUPLEX MATRIX PROBE")
    print("=" * 72)

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:
        print("IP inválido.")
        return

    probe = DuplexMatrixProbe(
        ip=ip,
        port=9100,
        timeout=5,
    )

    print()
    print(f"Impressora: {ip}")
    print("RAW:        9100")
    print()

    print("Este teste NÃO altera DEFAULT.")
    print()
    print("Serão enviados três jobs, cada um com duas páginas:")
    print()
    print("JOB A")
    print("  PJL SET DUPLEX=ON")
    print("  PCL sem comando explícito de duplex")
    print()
    print("JOB B")
    print("  PJL SET DUPLEX=OFF")
    print("  PCL DUPLEX=LONG EDGE")
    print()
    print("JOB C")
    print("  PJL SET DUPLEX=ON")
    print("  PCL DUPLEX=LONG EDGE")
    print()
    print("Total esperado: seis páginas.")
    print()

    confirmar = input(
        "A impressora irá imprimir. Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    original_corrente = probe.inquire("DUPLEX")
    original_default = probe.dinquire("DUPLEX")

    print()
    print("=" * 72)
    print("1. ESTADO ORIGINAL")
    print("=" * 72)

    print(f"INQUIRE  : {original_corrente}")
    print(f"DINQUIRE : {original_default}")

    # ==========================================================
    # TESTE PRELIMINAR DO SET
    # ==========================================================

    print()
    print("=" * 72)
    print("2. TESTE ISOLADO DE SET DUPLEX=ON")
    print("=" * 72)

    probe.set_variavel(
        "DUPLEX",
        "ON",
    )

    apos_set = probe.inquire("DUPLEX")
    apos_set_default = probe.dinquire("DUPLEX")

    print()
    print("Após SET:")
    print(f"INQUIRE  : {apos_set}")
    print(f"DINQUIRE : {apos_set_default}")

    if str(apos_set).upper() == "ON":
        print("✓ SET DUPLEX=ON é aceito pelo ambiente PJL.")
    else:
        print("✗ SET DUPLEX=ON não foi confirmado.")

    if str(apos_set_default).upper() == str(
        original_default
    ).upper():
        print("✓ DEFAULT permaneceu inalterado.")
    else:
        print("✗ DEFAULT foi alterado inesperadamente.")

    # Volta ao estado original
    probe.reset()

    corrente_pos_reset = probe.inquire("DUPLEX")
    default_pos_reset = probe.dinquire("DUPLEX")

    print()
    print("Após RESET:")
    print(f"INQUIRE  : {corrente_pos_reset}")
    print(f"DINQUIRE : {default_pos_reset}")

    # ==========================================================
    # JOB A
    # ==========================================================

    print()
    print("=" * 72)
    print("3. JOB A")
    print("=" * 72)

    print()
    print("PJL:")
    print("@PJL SET DUPLEX=ON")
    print()
    print("PCL:")
    print("(sem comando DUPLEX)")

    input(
        "Pressione ENTER para enviar o JOB A..."
    )

    bytes_a, tempo_a = probe.enviar_job(
        numero="A",
        duplex_pjl="ON",
        duplex_pcl=False,
    )

    print()
    print("JOB A enviado.")
    print(f"Bytes enviados: {bytes_a}")
    print(f"Tempo:          {tempo_a:.3f}s")

    print()
    print("Observe:")
    print("- duas páginas?")
    print("- uma folha frente e verso?")
    print("- acionamento do caminho duplex?")
    print()

    input(
        "Pressione ENTER para continuar..."
    )

    # ==========================================================
    # JOB B
    # ==========================================================

    print()
    print("=" * 72)
    print("4. JOB B")
    print("=" * 72)

    print()
    print("PJL:")
    print("@PJL SET DUPLEX=OFF")
    print()
    print("PCL:")
    print("ESC & l 1 S")
    print("(duplex long edge)")

    input(
        "Pressione ENTER para enviar o JOB B..."
    )

    bytes_b, tempo_b = probe.enviar_job(
        numero="B",
        duplex_pjl="OFF",
        duplex_pcl=True,
    )

    print()
    print("JOB B enviado.")
    print(f"Bytes enviados: {bytes_b}")
    print(f"Tempo:          {tempo_b:.3f}s")

    print()
    print("Observe se o job B entrou em duplex.")
    print()

    input(
        "Pressione ENTER para continuar..."
    )

    # ==========================================================
    # JOB C
    # ==========================================================

    print()
    print("=" * 72)
    print("5. JOB C")
    print("=" * 72)

    print()
    print("PJL:")
    print("@PJL SET DUPLEX=ON")
    print()
    print("PCL:")
    print("ESC & l 1 S")
    print("(duplex long edge)")

    input(
        "Pressione ENTER para enviar o JOB C..."
    )

    bytes_c, tempo_c = probe.enviar_job(
        numero="C",
        duplex_pjl="ON",
        duplex_pcl=True,
    )

    print()
    print("JOB C enviado.")
    print(f"Bytes enviados: {bytes_c}")
    print(f"Tempo:          {tempo_c:.3f}s")

    # ==========================================================
    # RESTAURAÇÃO
    # ==========================================================

    print()
    print("=" * 72)
    print("6. RESTAURAÇÃO")
    print("=" * 72)

    print()
    print("Enviando:")
    print("@PJL RESET")

    probe.reset()

    final_corrente = probe.inquire("DUPLEX")
    final_default = probe.dinquire("DUPLEX")

    print()
    print("Estado final:")
    print(f"INQUIRE  : {final_corrente}")
    print(f"DINQUIRE : {final_default}")

    print()
    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    print()
    print(f"Original corrente : {original_corrente}")
    print(f"Original default  : {original_default}")
    print(f"Final corrente    : {final_corrente}")
    print(f"Final default     : {final_default}")

    if (
        str(final_corrente).upper()
        == str(original_corrente).upper()
        and
        str(final_default).upper()
        == str(original_default).upper()
    ):
        print()
        print("✓ ESTADO PJL RESTAURADO.")
    else:
        print()
        print("✗ ESTADO FINAL DIFERE DO ORIGINAL.")

    print()
    print("=" * 72)
    print("INTERPRETAÇÃO FÍSICA")
    print("=" * 72)

    print()
    print("JOB A:")
    print("  PJL DUPLEX=ON")
    print("  PCL sem duplex")
    print()
    print("JOB B:")
    print("  PJL DUPLEX=OFF")
    print("  PCL DUPLEX=LONG EDGE")
    print()
    print("JOB C:")
    print("  PJL DUPLEX=ON")
    print("  PCL DUPLEX=LONG EDGE")
    print()
    print("Anote quantas folhas foram usadas em cada job")
    print("e se o mecanismo duplex foi acionado.")
    print()

    print("Nenhum DEFAULT foi alterado.")
    print()


if __name__ == "__main__":
    main()