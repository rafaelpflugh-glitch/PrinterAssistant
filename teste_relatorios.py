import requests
from bs4 import BeautifulSoup


ip="192.168.14.134"

url=f"http://{ip}/cgi-bin/dynamic/reports_and_information.html"


r=requests.get(url)


print(r.text[:5000])