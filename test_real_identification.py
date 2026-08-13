from core.session import Session

from modules.pjl import PJL


session = Session()


session.connect(

    "192.168.14.134"

)


pjl = PJL(session)



print("="*60)
print("INFO ID")
print("="*60)

print(
    pjl.info_id()
)



print()


print("="*60)
print("PRODINFO")
print("="*60)

print(
    pjl.prodinfo()
)



print()


print("="*60)
print("MEMORY")
print("="*60)

print(
    pjl.memory()
)