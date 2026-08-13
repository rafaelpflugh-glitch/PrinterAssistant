from core.session import Session

from modules.pjl import PJL

from parsers.pjl_parser import PJLParser

from reports.config_report import ConfigReport


session = Session()

session.connect(

    "192.168.14.134"

)

session.model = "Lexmark MX611dhe"

session.pagecount = 137974


pjl = PJL(session)

texto = pjl.config()

config = PJLParser.config(texto)


relatorio = ConfigReport()


print(

    relatorio.build(

        session,

        config

    )

)