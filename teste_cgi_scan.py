from tools.cgi_scanner import testar

ip="192.168.14.134"

lista=[

"/cgi-bin/script/printer/iop3",

"/cgi-bin/script/printer/scanmgr",

"/cgi-bin/script/printer/hostsend",

"/cgi-bin/script/printer/sysmgrdebugdata",

"/cgi-bin/script/printer/sysdebugdatarip",

"/cgi-bin/script/printer/healthcheckdebugdata",

"/cgi-bin/script/printer/usbhostscandata",

]

for e in lista:

    print(e)

    print(testar(ip,e))

    print()