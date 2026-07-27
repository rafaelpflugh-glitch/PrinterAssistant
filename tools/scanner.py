from tools.network import scan_rede
from core.printer import Printer
from tools.printer import PrinterDetector

import json
import os



def descobrir_impressoras(base):


    impressoras = []


    print()
    print("🔎 Procurando dispositivos...")
    print()


    ips = scan_rede(base)


    print(
        f"{len(ips)} dispositivos encontrados"
    )

    print()



    for ip in ips:


        print(
            "Analisando:",
            ip
        )


        try:


            # cria objeto da impressora
            printer = Printer(ip)


            # usa detector EWS
            detector = PrinterDetector(
                printer
            )


            resultado = detector.identificar()



            if resultado:


                impressoras.append(
                    printer
                )


                print()
                print(
                    "[IMPRESSORA]",
                    ip
                )


                print(
                    " Modelo:",
                    printer.modelo
                )


                print(
                    " Fabricante:",
                    printer.fabricante
                )


                print(
                    " Serial:",
                    printer.serial
                )


                print()



            else:


                print(
                    "Não identificada:",
                    ip
                )



        except Exception as erro:


            print()
            print(
                "ERRO:",
                ip
            )
            print(
                erro
            )



    salvar(
        impressoras
    )


    return impressoras





def salvar(lista):


    dados = []



    for p in lista:


        dados.append({

            "ip": p.ip,

            "hostname": p.hostname,

            "modelo": p.modelo,

            "fabricante": p.fabricante,

            "serial": p.serial

        })



    os.makedirs(
        "data",
        exist_ok=True
    )



    with open(
        "data/printers.json",
        "w",
        encoding="utf-8"
    ) as arquivo:


        json.dump(

            dados,

            arquivo,

            indent=4,

            ensure_ascii=False

        )