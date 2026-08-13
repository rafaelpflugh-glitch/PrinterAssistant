"""
Printer Assistant - PJL Persistent Write Probe

Testa, de forma controlada, DEFAULT em variáveis PJL simples
e reversíveis.

IMPORTANTE:
- Não usa SET como mecanismo principal.
- Descobre o valor original através de DINQUIRE.
- Testa DEFAULT.
- Confirma através de INQUIRE e DINQUIRE.
- Restaura o valor original.
- Confirma a restauração.
- Uma variável é testada por vez.
"""

from __future__ import annotations

import socket
import time


class PJLWriteProbe:
    def __init__(self, ip: str, port: int = 9100, timeout: float = 3.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def enviar(self, comando: str, espera: float = 0.20) -> str:
        sock = None

        try:
            sock = socket.create_connection(
                (self.ip, self.port),
                timeout=self.timeout,
            )

            sock.settimeout(self.timeout)

            if not comando.endswith("\r\n"):
                comando += "\r\n"

            sock.sendall(
                comando.encode(
                    "ascii",
                    errors="replace",
                )
            )

            if espera:
                time.sleep(espera)

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

    @staticmethod
    def extrair_valor(resposta: str):
        if not resposta:
            return None

        linhas = resposta.splitlines()

        for linha in linhas:
            linha = linha.strip()

            if not linha:
                continue

            if linha.upper().startswith("@PJL"):
                continue

            if "=" in linha:
                _, valor = linha.split("=", 1)
                return valor.strip().strip('"')

            return linha.strip('"')

        return None

    def inquire(self, variavel: str):
        resposta = self.enviar(
            f"@PJL INQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def dinquire(self, variavel: str):
        resposta = self.enviar(
            f"@PJL DINQUIRE {variavel}"
        )

        return self.extrair_valor(resposta)

    def default(self, variavel: str, valor: str):
        return self.enviar(
            f"@PJL DEFAULT {variavel}={valor}"
        )

    def estado(self, variavel: str):
        return {
            "inquire": self.inquire(variavel),
            "dinquire": self.dinquire(variavel),
        }


def iguais(a, b) -> bool:
    if a is None or b is None:
        return False

    return str(a).strip().upper() == str(b).strip().upper()


def escolher_teste(variavel: str, original: str):
    """
    Escolhe um valor alternativo conhecido e reversível.

    Nesta primeira bateria NÃO tentamos descobrir valores
    desconhecidos automaticamente.
    """

    valores = {
        "LANG": {
            "PORTUGUESE": "ENGLISH",
            "ENGLISH": "PORTUGUESE",
        },

        "DENSITY": {
            "1": "2",
            "2": "3",
            "3": "4",
            "4": "5",
            "5": "4",
        },

        "DUPLEX": {
            "OFF": "ON",
            "ON": "OFF",
        },

        "RESOLUTION": {
            "300": "600",
            "600": "1200",
            "1200": "600",
        },

        "ORIENTATION": {
            "PORTRAIT": "LANDSCAPE",
            "LANDSCAPE": "PORTRAIT",
        },
    }

    tabela = valores.get(variavel.upper())

    if tabela is None:
        return None

    return tabela.get(
        str(original).strip().upper()
    )


def testar_variavel(
    probe: PJLWriteProbe,
    variavel: str,
):
    print()
    print("=" * 72)
    print(f"TESTE: {variavel}")
    print("=" * 72)

    print()
    print(f"INQUIRE {variavel}")

    corrente_original = probe.inquire(variavel)

    print(
        f"Valor corrente original: "
        f"{corrente_original}"
    )

    print()
    print(f"DINQUIRE {variavel}")

    default_original = probe.dinquire(variavel)

    print(
        f"Valor default original:  "
        f"{default_original}"
    )

    if default_original is None:
        print()
        print(
            "⚠ Não foi possível descobrir "
            "o DEFAULT original."
        )
        print("Teste abortado para esta variável.")
        return

    valor_teste = escolher_teste(
        variavel,
        default_original,
    )

    if valor_teste is None:
        print()
        print(
            "⚠ Não existe valor de teste "
            "pré-definido para este estado."
        )
        print("Teste abortado para esta variável.")
        return

    print()
    print(f"Valor de teste: {valor_teste}")

    if iguais(
        valor_teste,
        default_original,
    ):
        print(
            "⚠ Valor de teste é igual ao original."
        )
        print("Teste abortado.")
        return

    print()
    print("-" * 72)
    print(
        f"1. DEFAULT {variavel}="
        f"{valor_teste}"
    )
    print("-" * 72)

    probe.default(
        variavel,
        valor_teste,
    )

    print()
    print(f"INQUIRE {variavel} após DEFAULT")

    corrente_teste = probe.inquire(variavel)

    print(
        f"Valor corrente: "
        f"{corrente_teste}"
    )

    print()
    print(f"DINQUIRE {variavel} após DEFAULT")

    default_teste = probe.dinquire(variavel)

    print(
        f"Valor default:  "
        f"{default_teste}"
    )

    corrente_ok = iguais(
        corrente_teste,
        valor_teste,
    )

    default_ok = iguais(
        default_teste,
        valor_teste,
    )

    print()

    if corrente_ok:
        print(
            f"✓ INQUIRE confirmou "
            f"{variavel}={valor_teste}"
        )
    else:
        print(
            f"⚠ INQUIRE NÃO confirmou "
            f"{variavel}={valor_teste}"
        )

    if default_ok:
        print(
            f"✓ DINQUIRE confirmou "
            f"{variavel}={valor_teste}"
        )
    else:
        print(
            f"⚠ DINQUIRE NÃO confirmou "
            f"{variavel}={valor_teste}"
        )

    print()
    print("-" * 72)
    print(
        f"2. RESTAURANDO DEFAULT "
        f"{variavel}={default_original}"
    )
    print("-" * 72)

    probe.default(
        variavel,
        default_original,
    )

    print()
    print(f"INQUIRE {variavel} final")

    corrente_final = probe.inquire(variavel)

    print(
        f"Valor corrente final: "
        f"{corrente_final}"
    )

    print()
    print(f"DINQUIRE {variavel} final")

    default_final = probe.dinquire(variavel)

    print(
        f"Valor default final:  "
        f"{default_final}"
    )

    restaurado_corrente = iguais(
        corrente_final,
        default_original,
    )

    restaurado_default = iguais(
        default_final,
        default_original,
    )

    print()

    if restaurado_corrente:
        print(
            "✓ INQUIRE restaurado."
        )
    else:
        print(
            "⚠ INQUIRE NÃO voltou "
            "ao valor original."
        )

    if restaurado_default:
        print(
            "✓ DINQUIRE restaurado."
        )
    else:
        print(
            "⚠ DINQUIRE NÃO voltou "
            "ao valor original."
        )

    print()
    print("-" * 72)
    print("RESULTADO")
    print("-" * 72)

    print(
        f"Original corrente : "
        f"{corrente_original}"
    )

    print(
        f"Original default  : "
        f"{default_original}"
    )

    print(
        f"Valor testado     : "
        f"{valor_teste}"
    )

    print(
        f"Após DEFAULT INQ  : "
        f"{corrente_teste}"
    )

    print(
        f"Após DEFAULT DINQ : "
        f"{default_teste}"
    )

    print(
        f"Final corrente    : "
        f"{corrente_final}"
    )

    print(
        f"Final default     : "
        f"{default_final}"
    )

    print()

    if default_ok and restaurado_default:
        print(
            f"✓ {variavel}: "
            "DEFAULT CONFIRMADO"
        )
    else:
        print(
            f"⚠ {variavel}: "
            "DEFAULT NÃO CONFIRMADO"
        )


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - PJL PERSISTENT WRITE PROBE")
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
        "Variáveis desta bateria:"
    )

    variaveis = [
        "LANG",
        "DENSITY",
        "DUPLEX",
        "RESOLUTION",
        "ORIENTATION",
    ]

    for variavel in variaveis:
        print(f"  - {variavel}")

    print()
    print(
        "IMPORTANTE:"
    )
    print(
        "Cada variável será alterada individualmente."
    )
    print(
        "O valor original será descoberto antes do teste."
    )
    print(
        "Após o teste, o valor original será restaurado."
    )
    print()

    confirmar = input(
        "Continuar? [S/N]: "
    ).strip().upper()

    if confirmar != "S":
        print("Teste cancelado.")
        return

    probe = PJLWriteProbe(
        ip=ip,
        port=9100,
        timeout=3,
    )

    print()
    print("=" * 72)
    print("INICIANDO BATERIA DE TESTES")
    print("=" * 72)

    try:
        for variavel in variaveis:
            try:
                testar_variavel(
                    probe,
                    variavel,
                )
            except Exception as exc:
                print()
                print(
                    f"⚠ ERRO AO TESTAR "
                    f"{variavel}: {exc}"
                )

    finally:
        print()
        print("=" * 72)
        print("BATERIA FINALIZADA")
        print("=" * 72)
        print()
        print(
            "Nenhuma variável deve permanecer "
            "alterada pelo teste."
        )
        print()


if __name__ == "__main__":
    main()