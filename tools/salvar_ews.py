import json


dados = {

    "modelo": "MX611",

    "ews": {

        "status":
        "/cgi-bin/dynamic/printer/PrinterStatus.html",


        "relatorios":
        "/cgi-bin/dynamic/reports_and_information.html",


        "configuracoes":
        "/cgi-bin/dynamic/config/config.html",


        "scanner":
        "/cgi-bin/dynamic/printer/config/scanprofile/createprofile.html",


        "painel_remoto":
        "/cgi-bin/dynamic/printer/config/remote_oppanel.html",


        "historico":
        "/cgi-bin/dynamic/printer/se/jobhistory.html",


        "sysdebug":
        "/cgi-bin/sysdebugdata",


        "usb_debug":
        "/cgi-bin/script/printer/usbhostscandata",


        "nvram":
        "/cgi-bin/nvram",


        "history":
        "/cgi-bin/history"

    }

}



with open(
    "database/models/mx611_ews.json",
    "w",
    encoding="utf-8"
) as f:


    json.dump(
        dados,
        f,
        indent=4,
        ensure_ascii=False
    )


print(
    "Mapa EWS salvo."
)