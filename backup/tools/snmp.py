from pysnmp.hlapi.v3arch.asyncio import *

import asyncio

COMMUNITY = "public"


async def snmp_get(ip, oid):
    try:

        iterator = get_cmd(
            SnmpEngine(),
            CommunityData(COMMUNITY),
            await UdpTransportTarget.create((ip, 161)),
            ContextData(),
            ObjectType(
                ObjectIdentity(oid)
            )
        )

        errorIndication, errorStatus, errorIndex, varBinds = await iterator

        if errorIndication:
            return None

        if errorStatus:
            return None

        for _, value in varBinds:
            return str(value)

    except Exception:
        return None


async def identificar(ip):

    dados = {}

    # Hostname
    dados["hostname"] = await snmp_get(
        ip,
        "1.3.6.1.2.1.1.5.0"
    )

    # Descrição completa
    dados["descricao"] = await snmp_get(
        ip,
        "1.3.6.1.2.1.1.1.0"
    )

    # Modelo (Printer-MIB)
    dados["modelo"] = await snmp_get(
        ip,
        "1.3.6.1.2.1.43.5.1.1.16.1"
    )

    # Serial (algumas Lexmark respondem aqui)
    dados["serial"] = await snmp_get(
        ip,
        "1.3.6.1.2.1.43.5.1.1.17.1"
    )

    # Firmware
    dados["firmware"] = dados["descricao"]

    return dados