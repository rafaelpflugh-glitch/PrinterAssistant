import socket


IP = "192.168.14.134"
PORTA = 9100
TIMEOUT = 5

UEL = b"\x1b%-12345X"


def enviar(comando):

    payload = (
        UEL
        + comando.encode("ascii")
        + b"\r\n"
        + UEL
    )

    resposta = b""

    with socket.create_connection(
        (IP, PORTA),
        timeout=TIMEOUT,
    ) as sock:

        sock.sendall(payload)

        while True:

            try:
                parte = sock.recv(8192)
            except socket.timeout:
                break

            if not parte:
                break

            resposta += parte

            if len(parte) < 8192:
                break

    return resposta.decode(
        "latin1",
        errors="ignore",
    )


print()
print("=" * 72)
print("TESTE PJL - IDIOMA DA MX611")
print("=" * 72)
print()

print("Idioma antes:")
print()

print(
    enviar("@PJL INFO VARIABLES")
)

print()
print("=" * 72)
print("ALTERANDO PARA NORWEGIAN")
print("=" * 72)
print()

print(
    enviar(
        "@PJL SET LANG=NORWEGIAN"
    )
)

print()
print("Idioma depois:")
print()

resultado = enviar(
    "@PJL INFO VARIABLES"
)

print(resultado)

print()
print("=" * 72)
print("FIM")
print("=" * 72)
print()