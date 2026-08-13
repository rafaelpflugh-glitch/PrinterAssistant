"""
Printer Assistant - Network Printer Discovery

Descoberta de impressoras Lexmark na rede local.

O IP é considerado temporário.
A identidade real deve ser determinada por informações
obtidas da própria impressora.

Este módulo NÃO altera configurações.
"""

import concurrent.futures
import ipaddress
import socket


class NetworkPrinterDiscovery:
    def __init__(
        self,
        timeout=0.35,
        port=9100,
        max_workers=64,
    ):
        self.timeout = timeout
        self.port = port
        self.max_workers = max_workers

    def discover(self, network):
        """
        Descobre hosts que aceitam conexão TCP na porta RAW 9100.

        Exemplo:
            discovery.discover("192.168.14.0/24")
        """

        rede = ipaddress.ip_network(
            network,
            strict=False,
        )

        enderecos = [
            str(ip)
            for ip in rede.hosts()
        ]

        encontrados = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            futuros = {
                executor.submit(
                    self._testar_porta,
                    ip,
                ): ip
                for ip in enderecos
            }

            for futuro in concurrent.futures.as_completed(
                futuros
            ):
                ip = futuros[futuro]

                try:
                    resultado = futuro.result()
                except Exception:
                    resultado = None

                if resultado:
                    encontrados.append(
                        resultado
                    )

        encontrados.sort(
            key=lambda item: item["ip"]
        )

        return encontrados

    def _testar_porta(self, ip):
        """
        Testa somente conectividade TCP.
        Não presume que todo host:9100 seja impressora.
        """

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.settimeout(
            self.timeout
        )

        try:
            resultado = sock.connect_ex(
                (ip, self.port)
            )

            if resultado != 0:
                return None

            return {
                "ip": ip,
                "porta": self.port,
                "raw": True,
            }

        finally:
            sock.close()

    @staticmethod
    def detectar_rede_local():
        """
        Tenta descobrir automaticamente a rede IPv4
        associada ao computador.

        Retorna algo como:
            192.168.14.0/24

        Caso não seja possível determinar a rede,
        retorna None.
        """

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.connect(
                ("8.8.8.8", 80)
            )

            ip_local = sock.getsockname()[0]

        except OSError:
            return None

        finally:
            sock.close()

        partes = ip_local.split(".")

        if len(partes) != 4:
            return None

        return (
            f"{partes[0]}."
            f"{partes[1]}."
            f"{partes[2]}."
            f"0/24"
        )


def main():
    print("=" * 72)
    print("PRINTER ASSISTANT - NETWORK PRINTER DISCOVERY")
    print("=" * 72)

    rede = input(
        "Rede IPv4 "
        "(ENTER = detectar automaticamente): "
    ).strip()

    if not rede:
        rede = NetworkPrinterDiscovery.detectar_rede_local()

    if not rede:
        print(
            "Não foi possível determinar "
            "a rede local."
        )
        return

    print()
    print(f"Rede: {rede}")
    print("Porta RAW: 9100")
    print()
    print("Procurando hosts...")
    print()

    discovery = NetworkPrinterDiscovery()

    encontrados = discovery.discover(
        rede
    )

    if not encontrados:
        print(
            "Nenhum host respondeu na "
            "porta RAW 9100."
        )
        return

    print(
        f"Hosts encontrados: "
        f"{len(encontrados)}"
    )

    print()

    for item in encontrados:
        print(
            f"{item['ip']}:{item['porta']}"
        )


if __name__ == "__main__":
    main()