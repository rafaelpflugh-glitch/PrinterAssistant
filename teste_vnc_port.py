import socket


ip="192.168.14.134"

porta=5900


print("==============================")
print("TESTANDO VNC")
print("==============================")


s=socket.socket()

s.settimeout(5)


try:

    s.connect(
        (ip,porta)
    )

    print(
        "PORTA ABERTA"
    )

    banner=s.recv(100)

    print(
        banner
    )


except Exception as e:

    print(
        "ERRO:",
        e
    )


finally:

    s.close()