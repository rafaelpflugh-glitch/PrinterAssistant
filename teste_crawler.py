from core.knowledge.crawler import EWSCrawler

ip = "192.168.14.134"

crawler = EWSCrawler(ip)

paginas = crawler.explorar()

print()

print("="*40)

print("TOTAL")

print("="*40)

print(len(paginas))

print()

for p in paginas:

    print(p)