from core.tool import Tool

from modules.pjl import PJL


def executar(session, **kwargs):

    pjl = PJL(session)

    print()

    print(
        pjl.status()
    )


tool = Tool(

    id="pjl_status",

    name="Status PJL",

    description="Consulta status da impressora.",

    category="PJL",

    manufacturer=None,

    family=None,

    models=[],

    requires_session=True,

    callback=executar

)