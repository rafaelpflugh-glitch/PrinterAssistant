from pjl.client import PJLClient
from pjl import commands

IP = "192.168.14.134"

pjl = PJLClient(IP)

print()

print("=" * 60)
print("TESTE PJL")
print("=" * 60)

print()

print("INFO ID")

print()

print(

    pjl.send(

        commands.INFO_ID

    )

)

print()

print("=" * 60)