import asyncio
import re

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    walk_cmd
)


IP = "192.168.14.134"
COMMUNITY = "public"


OIDS_TESTE = {

    "Printer-MIB supplies":
        "1.3.6.1.2.1.43.11",

    "Printer-MIB marker":
        "1.3.6.1.2.1.43.10",

    "Printer-MIB marker table":
        "1.3.6.1.2.1.43.5",

    "Lexmark enterprise":
        "1.3.6.1.4.1.641",

}


def limpar(valor):

    try:
        return valor.prettyPrint()

    except:

        return str(valor)



def parece_serial(texto):

    if not texto:
        return False

    texto = texto.upper()

    padroes = [

        r"\bCAS[A-Z0-9]+\b",
        r"\bCAD[A-Z0-9]+\b",
        r"\bCAB[A-Z0-9]+\b",
        r"\bET[A-Z0-9]+\b",

    ]

    for p in padroes:

        if re.search(p, texto):

            return True

    return False



async def target():

    return await UdpTransportTarget.create(
        (IP,161),
        timeout=3,
        retries=1
    )



async def walk(oid_nome, oid):

    print()
    print("="*80)
    print(oid_nome)
    print(oid)
    print("="*80)

    encontrado = 0

    try:

        iterator = walk_cmd(

            SnmpEngine(),

            CommunityData(
                COMMUNITY,
                mpModel=1
            ),

            await target(),

            ContextData(),

            ObjectType(
                ObjectIdentity(
                    oid
                )
            ),

            lexicographicMode=False,

            lookupMib=False

        )


        async for erro, status, _, binds in iterator:


            if erro:

                print(
                    "ERRO:",
                    erro
                )

                break


            if status:

                print(
                    "STATUS:",
                    status
                )

                break


            for oid_resultado, valor in binds:

                o = str(oid_resultado)

                v = limpar(valor)


                print(
                    o,
                    "=>",
                    v
                )


                if parece_serial(v):

                    print(
                        "\n*** POSSÍVEL SERIAL ENCONTRADO ***"
                    )

                    print(
                        o,
                        "=>",
                        v
                    )

                    encontrado += 1



    except Exception as e:

        print(
            "FALHA:",
            e
        )


    print()

    print(
        "Encontrados:",
        encontrado
    )




async def main():


    print()
    print("="*80)
    print("DEBUG SERIAL CONSUMÍVEIS - PRINTER ASSISTANT")
    print("="*80)

    print(
        "IP:",
        IP
    )


    for nome, oid in OIDS_TESTE.items():

        await walk(
            nome,
            oid
        )


    print()
    print("="*80)
    print("FIM")
    print("="*80)




if __name__ == "__main__":

    asyncio.run(main())