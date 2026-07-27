def parse_hostname(snmp_data):

    for oid, value in snmp_data:

        if oid == "1.3.6.1.2.1.1.5.0":
            return value

    return "Desconhecido"



def parse_model(snmp_data):

    for oid, value in snmp_data:

        if oid.startswith(
            "1.3.6.1.2.1.43.15.1.1.4"
        ):
            return value

    return "Desconhecido"



def parse_description(snmp_data):

    for oid, value in snmp_data:

        if oid == "1.3.6.1.2.1.1.1.0":
            return value

    return "Desconhecido"