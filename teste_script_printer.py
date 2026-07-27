import requests

ip="192.168.14.134"

lista=[
"iop3",
"scanmgr",
"hostsend",
"sysmgrdebugdata",
"healthcheckdebugdata",
"rapdebugdata",
"usbhostscandata",
"fwdbgsvcrdump0",
"fwdbgsvcrdump1",
"fwdbgsvcrdump2",
"lbtracedumprip",
"printkdumprip",
"sysdebugdatarip",
]

for item in lista:

    url=f"http://{ip}/cgi-bin/script/printer/{item}"

    try:

        r=requests.get(url,timeout=8)

        print(r.status_code,item,len(r.text))

    except:

        pass