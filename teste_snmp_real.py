import asyncio

from tools.snmp import snmp_get



IP="192.168.14.134"



async def main():

    hostname = await snmp_get(
        IP,
        "1.3.6.1.2.1.1.5.0"
    )


    descricao = await snmp_get(
        IP,
        "1.3.6.1.2.1.1.1.0"
    )


    print("Hostname:")
    print(hostname)


    print()

    print("Descricao:")
    print(descricao)



asyncio.run(main())