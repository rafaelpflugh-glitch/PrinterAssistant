
"""
Comunicação com a TSC.
"""

import socket


LABEL_IP = "192.168.14.151"

LABEL_PORT = 9100


class TSCPrinter:

    def print(self, tspl):

        with socket.create_connection(

            (
                LABEL_IP,
                LABEL_PORT
            ),

            timeout=5

        ) as sock:

            sock.sendall(

                tspl.encode(

                    "ascii",

                    errors="replace"

                )

            )

        return True