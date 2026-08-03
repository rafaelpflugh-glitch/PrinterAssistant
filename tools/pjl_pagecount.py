from core.tool import Tool

from modules.pjl import PJL


def executar(session, **kwargs):

    pjl = PJL(session)

    print()

    print(

        pjl.pagecount()

    )


tool = Tool(

    id="pjl_pagecount",

    name="Contador",

    description="Consulta contador.",

    category="PJL",

    manufacturer=None,

    family=None,

    models=[],

    requires_session=True,

    callback=executar

)