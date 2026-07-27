from core.sniffer import FormSniffer
import json

ip = "192.168.14.134"

endpoint = "/cgi-bin/dynamic/printer/config/reports/deviceinfo.html"

sniffer = FormSniffer(ip)

forms = sniffer.analisar(endpoint)

print()

print("="*50)

print("FORMULÁRIOS")

print("="*50)

print()

print(json.dumps(

    forms,

    indent=4,

    ensure_ascii=False

))