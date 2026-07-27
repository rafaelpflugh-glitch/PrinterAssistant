from pysnmp.hlapi import *


ip = "192.168.14.134"


print("=== SNMP LEXMARK WALK ===")


for (
    errorIndication,
    errorStatus,
    errorIndex,
    varBinds

) in nextCmd(
    SnmpEngine(),
    CommunityData("public"),
    UdpTransportTarget((ip,161)),
    ContextData(),
    ObjectType(
        ObjectIdentity(
            "1.3.6.1.2.1.43"
        )
    ),
    lexicographicMode=False
):

    if errorIndication:
        print(errorIndication)
        break

    elif errorStatus:
        print(
            errorStatus.prettyPrint()
        )
        break

    else:

        for name,value in varBinds:

            print(
                name.prettyPrint(),
                "=",
                value.prettyPrint()
            )