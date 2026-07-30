import socket
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor


def ping(ip):

    sistema = platform.system().lower()

    if sistema == "windows":

        comando = [
            "ping",
            "-n",
            "1",
            "-w",
            "300",
            ip
        ]

    else:

        comando = [
            "ping",
            "-c",
            "1",
            "-W",
            "1",
            ip
        ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return resultado.returncode == 0


def porta_aberta(ip, porta, timeout=0.3):

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    sock.settimeout(timeout)

    try:

        sock.connect((ip, porta))

        sock.close()

        return True

    except:

        return False


def scan_rede(base):

    ativos = []

    ips = [
        f"{base}.{i}"
        for i in range(1,255)
    ]

    with ThreadPoolExecutor(max_workers=64) as pool:

        resultados = pool.map(
            ping,
            ips
        )

        for ip, ok in zip(ips, resultados):

            if ok:

                ativos.append(ip)

    return ativos