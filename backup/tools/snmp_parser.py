import re


def parse_snmp_supplies(snmp_data):
    """
    Recebe uma lista de tuplas SNMP (oid, valor)
    e retorna suprimentos organizados
    """

    supplies = {}

    for oid, value in snmp_data:

        # Nome do suprimento
        if ".43.11.1.1.6." in oid:

            index = oid.split(".")[-1]

            if index not in supplies:
                supplies[index] = {}

            supplies[index]["nome"] = value


        # Capacidade
        elif ".43.11.1.1.8." in oid:

            index = oid.split(".")[-1]

            if index not in supplies:
                supplies[index] = {}

            try:
                supplies[index]["capacidade"] = int(value)

            except:
                supplies[index]["capacidade"] = 0


        # Restante
        elif ".43.11.1.1.9." in oid:

            index = oid.split(".")[-1]

            if index not in supplies:
                supplies[index] = {}

            try:
                supplies[index]["restante"] = int(value)

            except:
                supplies[index]["restante"] = 0



    # calcula porcentagem

    for item in supplies.values():

        try:

            capacidade = item.get("capacidade", 0)
            restante = item.get("restante", 0)

            if capacidade > 0:

                item["nivel"] = round(
                    restante /
                    capacidade *
                    100
                )

            else:

                item["nivel"] = None


        except:

            item["nivel"] = None



    return list(supplies.values())





def parse_device_info(snmp_data):
    """
    Extrai identificação real da impressora
    usando System MIB
    """

    info = {

        "fabricante": "Desconhecido",
        "modelo": "Desconhecido",
        "firmware": "Desconhecido",
        "hostname": "Desconhecido"

    }


    for oid, value in snmp_data:


        # SysDescr
        # Ex:
        # Lexmark MX611dhe version NH7.SB.N022 kernel...

        if oid == "1.3.6.1.2.1.1.1.0":


            partes = value.split()


            if len(partes) > 0:

                info["fabricante"] = partes[0]


            if len(partes) > 1:

                info["modelo"] = partes[1]


            if "version" in partes:

                pos = partes.index("version")


                if len(partes) > pos + 1:

                    info["firmware"] = partes[pos + 1]



        # Hostname

        elif oid == "1.3.6.1.2.1.1.5.0":

            info["hostname"] = value



    return info





def parse_model(snmp_data):
    """
    Compatibilidade com versões antigas.
    Agora usa SysDescr ao invés do Printer-MIB.
    """

    info = parse_device_info(snmp_data)

    return info["modelo"]





def parse_hostname(snmp_data):

    for oid, value in snmp_data:

        if oid == "1.3.6.1.2.1.1.5.0":

            return value


    return "Desconhecido"