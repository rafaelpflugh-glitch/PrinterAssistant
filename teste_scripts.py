import requests

ip = "192.168.14.134"

scripts = [
"scanmgr",
"hostsend",
"sysmgrdebugdata",
"healthcheckdebugdata",
"rapdebugdata",
"faxsetup",
"faxlog",
"faxjoblog",
"faxcalllog",
"prtappse",
"solnmgmtdata",
"xclib",
"security_se",
"guidebugdata",
"guimemdebugdata",
"objstoredebugdata"
]

for s in scripts:

    print("="*70)
    print(s)

    try:

        r = requests.get(
            f"http://{ip}/cgi-bin/script/printer/{s}",
            timeout=5
        )

        print("STATUS:", r.status_code)
        print(r.text[:500])

    except Exception as e:
        print(e)