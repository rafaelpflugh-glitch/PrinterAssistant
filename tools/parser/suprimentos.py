def parse_snmp_supplies(snmp_data):

    supplies = {}


    for oid,value in snmp_data:


        if ".43.11.1.1.6." in oid:

            index = oid.split(".")[-1]

            supplies.setdefault(index,{})
            supplies[index]["nome"] = value



        elif ".43.11.1.1.8." in oid:

            index = oid.split(".")[-1]

            supplies.setdefault(index,{})
            supplies[index]["capacidade"] = int(value)



        elif ".43.11.1.1.9." in oid:

            index = oid.split(".")[-1]

            supplies.setdefault(index,{})
            supplies[index]["restante"] = int(value)



    resultado=[]


    for item in supplies.values():

        try:

            item["nivel"] = round(
                item["restante"] /
                item["capacidade"] *
                100
            )

        except:

            item["nivel"] = None


        resultado.append(item)


    return resultado