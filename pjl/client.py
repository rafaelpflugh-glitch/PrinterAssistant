import socket


class PJLClient:

    def __init__(

        self,

        ip,

        port=9100,

        timeout=5

    ):

        self.ip = ip
        self.port = port
        self.timeout = timeout


    def send(self, comando):

        try:

            with socket.create_connection(

                (self.ip, self.port),

                timeout=self.timeout

            ) as sock:

                sock.sendall(

                    (
                        "\x1b%-12345X"
                        + comando
                        + "\r\n"
                        + "\x1b%-12345X"
                    ).encode()

                )

                resposta = b""

                sock.settimeout(2)

                while True:

                    try:

                        bloco = sock.recv(4096)

                        if not bloco:

                            break

                        resposta += bloco

                    except socket.timeout:

                        break

                return resposta.decode(

                    errors="ignore"

                )

        except Exception as erro:

            return f"[PJL ERRO] {erro}"