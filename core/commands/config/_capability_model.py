"""
PRINTER ASSISTANT
MX611 CAPABILITY MODEL

Modelo consolidado das capacidades descobertas
empiricamente na Lexmark MX611dhe.

IMPORTANTE:

Este arquivo NAO conversa com a impressora.

Ele representa conhecimento ja confirmado
pelos probes de descoberta e comportamento.

Os estados de capacidade distinguem:

- UNKNOWN
- QUERY_ONLY
- CONFIRMED
- JOB_CONFIRMED
- PHYSICAL_CONFIRMED
- UNSUPPORTED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# ESTADOS DE CAPACIDADE
# ============================================================

STATUS_UNKNOWN = "UNKNOWN"
STATUS_QUERY_ONLY = "QUERY_ONLY"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_JOB_CONFIRMED = "JOB_CONFIRMED"
STATUS_PHYSICAL_CONFIRMED = "PHYSICAL_CONFIRMED"
STATUS_UNSUPPORTED = "UNSUPPORTED"


# ============================================================
# TIPOS
# ============================================================


@dataclass
class Capability:
    name: str

    # Estado consolidado da capacidade.
    status: str = STATUS_UNKNOWN

    # A variavel/comando existe no ambiente PJL?
    supported: bool = False

    # SET foi confirmado atraves de INQUIRE?
    set_confirmed: bool = False

    # O comportamento dentro de um job foi confirmado?
    job_confirmed: bool = False

    # O efeito real foi confirmado fisicamente?
    behavior_confirmed: bool = False

    # RESET voltou ao estado original?
    reset_confirmed: bool = False

    # DEFAULT permaneceu intacto?
    default_preserved: bool = True

    # Observacao tecnica.
    notes: str = ""

    # Valores conhecidos.
    values: list[str] = field(default_factory=list)


@dataclass
class InfoCapability:
    name: str
    supported: bool
    response: bool = False
    notes: str = ""


@dataclass
class CapabilityModel:
    manufacturer: str
    model: str
    raw_port: int

    # Identidade.
    identity: dict[str, Any] = field(default_factory=dict)

    # INFO PJL.
    info: dict[str, InfoCapability] = field(default_factory=dict)

    # USTATUS.
    ustatus: dict[str, Capability] = field(default_factory=dict)

    # Variaveis PJL conhecidas.
    variables: dict[str, Capability] = field(default_factory=dict)

    # Controles de impressao.
    print_controls: dict[str, Capability] = field(default_factory=dict)

    # Capacidades fisicas.
    physical: dict[str, Any] = field(default_factory=dict)

    # Observacoes gerais.
    notes: list[str] = field(default_factory=list)


# ============================================================
# BUILDER PRINCIPAL
# ============================================================


def build_mx611_capability_model() -> CapabilityModel:
    """
    Retorna o modelo consolidado da Lexmark MX611dhe
    baseado nos testes ja realizados.
    """

    model = CapabilityModel(
        manufacturer="Lexmark",
        model="MX611dhe",
        raw_port=9100,
    )

    # ========================================================
    # IDENTIDADE
    # ========================================================

    model.identity = {
        "id": "Lexmark MX611dhe",
        "serial_number": "701644HH03ND3",
        "system_firmware": "LW70.SB7.P022-800",
        "scanner_firmware": "LW70.SB7.P022 -LW70.SB7.P022",
        "scanner_boot_firmware": "-LW70.SB7.P022",
        "scanner_duplex_firmware": "-LW70.SB7.P022",
        "font_firmware": "8.31M02-U5.021",
        "engine_firmware": "FDN.PIR.E704-0",
        "engine_speed": 50,
    }

    # ========================================================
    # INFO PJL
    # ========================================================

    model.info = {
        "ID": InfoCapability(
            name="INFO ID",
            supported=True,
            response=True,
            notes="Identificacao da impressora confirmada.",
        ),

        "STATUS": InfoCapability(
            name="INFO STATUS",
            supported=True,
            response=True,
            notes=(
                'Retorna CODE=10001, DISPLAY="Pronto", '
                "ONLINE=TRUE."
            ),
        ),

        "PAGECOUNT": InfoCapability(
            name="INFO PAGECOUNT",
            supported=True,
            response=True,
            notes="Contador total de paginas confirmado.",
        ),

        "MEMORY": InfoCapability(
            name="INFO MEMORY",
            supported=True,
            response=True,
            notes="Retorna TOTAL e LARGEST.",
        ),

        "VARIABLES": InfoCapability(
            name="INFO VARIABLES",
            supported=True,
            response=True,
            notes=(
                "Retorna variaveis PJL configuraveis "
                "e seus valores."
            ),
        ),

        "USTATUS": InfoCapability(
            name="INFO USTATUS",
            supported=True,
            response=True,
            notes=(
                "Retorna DEVICE, JOB, PAGE e TIMED."
            ),
        ),

        "CONFIG": InfoCapability(
            name="INFO CONFIG",
            supported=True,
            response=True,
            notes=(
                "Retorna capacidades fisicas, "
                "bandejas, papeis e linguagens."
            ),
        ),

        "PRODINFO": InfoCapability(
            name="INFO PRODINFO",
            supported=False,
            response=False,
            notes="Nenhuma resposta observada.",
        ),

        "FILESYS": InfoCapability(
            name="INFO FILESYS",
            supported=False,
            response=False,
            notes="Nenhuma resposta observada.",
        ),
    }

    # ========================================================
    # USTATUS
    # ========================================================

    model.ustatus = {
        "DEVICE": Capability(
            name="USTATUS DEVICE",
            status=STATUS_QUERY_ONLY,
            supported=True,
            notes=(
                "INFO USTATUS declara DEVICE como "
                "suportado. Captura de eventos ainda "
                "nao foi confirmada."
            ),
            values=[
                "OFF",
                "ON",
                "VERBOSE",
            ],
        ),

        "JOB": Capability(
            name="USTATUS JOB",
            status=STATUS_QUERY_ONLY,
            supported=True,
            notes=(
                "INFO USTATUS declara JOB como suportado. "
                "Captura de eventos ainda nao foi confirmada."
            ),
            values=[
                "OFF",
                "ON",
            ],
        ),

        "PAGE": Capability(
            name="USTATUS PAGE",
            status=STATUS_QUERY_ONLY,
            supported=True,
            notes=(
                "INFO USTATUS declara PAGE como suportado. "
                "Captura de eventos ainda nao foi confirmada."
            ),
            values=[
                "OFF",
                "ON",
            ],
        ),

        "TIMED": Capability(
            name="USTATUS TIMED",
            status=STATUS_QUERY_ONLY,
            supported=True,
            notes=(
                "INFO USTATUS declara intervalo "
                "entre 5 e 300. Comportamento ainda "
                "nao foi confirmado."
            ),
            values=[
                "5-300",
            ],
        ),
    }

    # ========================================================
    # VARIAVEIS PJL DESCOBERTAS
    # ========================================================

    model.variables = {

        # ----------------------------------------------------
        # PAPER
        # ----------------------------------------------------

        "PAPER": Capability(
            name="PAPER",
            status=STATUS_CONFIRMED,
            supported=True,
            set_confirmed=True,
            reset_confirmed=True,
            behavior_confirmed=True,
            notes=(
                "SET PAPER=A5 alterou INQUIRE para A5; "
                "DINQUIRE permaneceu A4; RESET restaurou A4."
            ),
            values=[
                "LETTER",
                "LEGAL",
                "A4",
                "A5",
                "A6",
                "JISB5",
                "CUSTOM",
                "EXECUTIVE",
                "FOLIO",
                "OFICIO",
                "STATEMENT",
                "COM10",
                "COM9",
                "MONARCH",
                "DL",
                "C5",
                "B5",
                "OTHERENVELOPE",
            ],
        ),

        # ----------------------------------------------------
        # MEDIATYPE
        # ----------------------------------------------------

        "MEDIATYPE": Capability(
            name="MEDIATYPE",
            status=STATUS_CONFIRMED,
            supported=True,
            set_confirmed=True,
            reset_confirmed=True,
            behavior_confirmed=False,
            notes=(
                "SET MEDIATYPE foi aceito e RESET foi "
                "confirmado. O comportamento fisico "
                "especifico ainda nao foi isoladamente "
                "confirmado."
            ),
            values=[
                "PLAIN",
            ],
        ),

        # ----------------------------------------------------
        # DUPLEX
        # ----------------------------------------------------

        "DUPLEX": Capability(
            name="DUPLEX",
            status=STATUS_PHYSICAL_CONFIRMED,
            supported=True,
            set_confirmed=True,
            job_confirmed=True,
            behavior_confirmed=True,
            reset_confirmed=True,
            notes=(
                "SET DUPLEX=ON/OFF foi aceito. "
                "Jobs de duas paginas confirmaram "
                "fisicamente o funcionamento do duplex."
            ),
            values=[
                "OFF",
                "ON",
            ],
        ),

        # ----------------------------------------------------
        # COPIES
        # ----------------------------------------------------

        "COPIES": Capability(
            name="COPIES",
            status=STATUS_PHYSICAL_CONFIRMED,
            supported=True,
            set_confirmed=True,
            job_confirmed=True,
            behavior_confirmed=True,
            reset_confirmed=True,
            notes=(
                "COPIES=2 foi testado com uma unica pagina "
                "PCL e confirmou comportamento de copias."
            ),
            values=[
                "1-999",
            ],
        ),

        # ----------------------------------------------------
        # RESOLUTION
        # ----------------------------------------------------

        "RESOLUTION": Capability(
            name="RESOLUTION",
            status=STATUS_PHYSICAL_CONFIRMED,
            supported=True,
            set_confirmed=False,
            job_confirmed=True,
            behavior_confirmed=True,
            reset_confirmed=True,
            notes=(
                "INQUIRE permaneceu 600 apos SET 1200, "
                "mas a alteracao de qualidade foi visivel "
                "fisicamente entre os jobs. "
                "O efeito real foi confirmado mesmo sem "
                "confirmacao por INQUIRE."
            ),
            values=[
                "600",
                "1200",
            ],
        ),

        # ----------------------------------------------------
        # DENSITY
        # ----------------------------------------------------

        "DENSITY": Capability(
            name="DENSITY",
            status=STATUS_PHYSICAL_CONFIRMED,
            supported=True,
            set_confirmed=False,
            job_confirmed=True,
            behavior_confirmed=True,
            reset_confirmed=True,
            notes=(
                "INQUIRE permaneceu 3 apos SET 4, "
                "mas a diferenca de qualidade/densidade "
                "foi visivel fisicamente."
            ),
            values=[
                "1-5",
            ],
        ),

        # ----------------------------------------------------
        # ORIENTATION
        # ----------------------------------------------------

        "ORIENTATION": Capability(
            name="ORIENTATION",
            status=STATUS_PHYSICAL_CONFIRMED,
            supported=True,
            set_confirmed=False,
            job_confirmed=True,
            behavior_confirmed=True,
            reset_confirmed=True,
            notes=(
                "INQUIRE permaneceu PORTRAIT apos SET "
                "LANDSCAPE, mas a pagina do job foi "
                "fisicamente impressa em LANDSCAPE."
            ),
            values=[
                "PORTRAIT",
                "LANDSCAPE",
            ],
        ),

        # ----------------------------------------------------
        # LANG
        # ----------------------------------------------------

        "LANG": Capability(
            name="LANG",
            status=STATUS_QUERY_ONLY,
            supported=True,
            set_confirmed=False,
            reset_confirmed=True,
            notes=(
                "SET LANG=ENGLISH nao alterou INQUIRE. "
                "Valor observado: PORTUGUESE."
            ),
            values=[
                "PORTUGUESE",
            ],
        ),

        # ----------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------

        "LANGUAGE": Capability(
            name="LANGUAGE",
            status=STATUS_QUERY_ONLY,
            supported=True,
            set_confirmed=False,
            reset_confirmed=True,
            notes=(
                "SET LANGUAGE=ENGLISH nao alterou INQUIRE. "
                "Valor observado: PORTUGUESE."
            ),
            values=[
                "PORTUGUESE",
            ],
        ),

        # ----------------------------------------------------
        # TIMEZONE
        # ----------------------------------------------------

        "TIMEZONE": Capability(
            name="TIMEZONE",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # COUNTRY
        # ----------------------------------------------------

        "COUNTRY": Capability(
            name="COUNTRY",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # COUNTRYCODE
        # ----------------------------------------------------

        "COUNTRYCODE": Capability(
            name="COUNTRYCODE",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # OUTPUTBIN
        # ----------------------------------------------------

        "OUTPUTBIN": Capability(
            name="OUTPUTBIN",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # MEDIASOURCE
        # ----------------------------------------------------

        "MEDIASOURCE": Capability(
            name="MEDIASOURCE",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes=(
                'INQUIRE retorna "?" ou resposta '
                "inconsistente."
            ),
        ),

        # ----------------------------------------------------
        # TRAY
        # ----------------------------------------------------

        "TRAY": Capability(
            name="TRAY",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # INPUTTRAY
        # ----------------------------------------------------

        "INPUTTRAY": Capability(
            name="INPUTTRAY",
            status=STATUS_UNSUPPORTED,
            supported=False,
            set_confirmed=False,
            reset_confirmed=True,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # MEDIAWEIGHT
        # ----------------------------------------------------

        "MEDIAWEIGHT": Capability(
            name="MEDIAWEIGHT",
            status=STATUS_UNSUPPORTED,
            supported=False,
            notes='INQUIRE retorna "?".',
        ),

        # ----------------------------------------------------
        # MEDIATEXTURE
        # ----------------------------------------------------

        "MEDIATEXTURE": Capability(
            name="MEDIATEXTURE",
            status=STATUS_UNSUPPORTED,
            supported=False,
            notes='INQUIRE retorna "?".',
        ),
    }

    # ========================================================
    # CONTROLES DE IMPRESSAO
    # ========================================================

    model.print_controls = {
        "COPIES": model.variables["COPIES"],
        "DUPLEX": model.variables["DUPLEX"],
        "RESOLUTION": model.variables["RESOLUTION"],
        "DENSITY": model.variables["DENSITY"],
        "ORIENTATION": model.variables["ORIENTATION"],
        "PAPER": model.variables["PAPER"],
        "MEDIATYPE": model.variables["MEDIATYPE"],
    }

    # ========================================================
    # CAPACIDADES FISICAS
    # ========================================================

    model.physical = {
        "duplex": True,
        "languages": [
            "PCL",
            "POSTSCRIPT",
        ],
        "input_trays": [
            "TRAY1",
            "MPFEEDER",
            "ENVELOPE TRAY",
        ],
        "output_bins": [
            "UPPER FACEDOWN",
        ],
        "engine_speed_ppm": 50,
        "memory_reported": 1073741824,
        "disk_reported": 319426613248,
    }

    # ========================================================
    # OBSERVACOES
    # ========================================================

    model.notes = [
        "MX611dhe identificada via PJL INFO ID.",
        (
            "INFO STATUS, PAGECOUNT, MEMORY, VARIABLES, "
            "USTATUS e CONFIG respondem."
        ),
        "INFO PRODINFO nao apresentou resposta.",
        "INFO FILESYS nao apresentou resposta.",
        "PAPER possui SET/RESET confirmado.",
        "MEDIATYPE possui SET/RESET confirmado.",
        "DUPLEX possui comportamento fisico confirmado.",
        "COPIES possui comportamento fisico confirmado.",
        (
            "RESOLUTION possui efeito fisico confirmado "
            "apesar de INQUIRE permanecer 600."
        ),
        (
            "DENSITY possui efeito fisico confirmado "
            "apesar de INQUIRE permanecer 3."
        ),
        (
            "ORIENTATION possui efeito fisico confirmado "
            "apesar de INQUIRE permanecer PORTRAIT."
        ),
        (
            "USTATUS declara DEVICE, JOB, PAGE e TIMED, "
            "mas captura de eventos ainda nao foi confirmada."
        ),
        "Nenhum DEFAULT foi alterado pelos testes realizados.",
    ]

    return model


# ============================================================
# FUNCOES AUXILIARES
# ============================================================


def capability_to_dict(cap: Capability) -> dict[str, Any]:
    return {
        "name": cap.name,
        "status": cap.status,
        "supported": cap.supported,
        "set_confirmed": cap.set_confirmed,
        "job_confirmed": cap.job_confirmed,
        "behavior_confirmed": cap.behavior_confirmed,
        "reset_confirmed": cap.reset_confirmed,
        "default_preserved": cap.default_preserved,
        "notes": cap.notes,
        "values": cap.values,
    }


def model_to_dict(model: CapabilityModel) -> dict[str, Any]:
    return {
        "manufacturer": model.manufacturer,
        "model": model.model,
        "raw_port": model.raw_port,
        "identity": model.identity,

        "info": {
            name: {
                "name": value.name,
                "supported": value.supported,
                "response": value.response,
                "notes": value.notes,
            }
            for name, value in model.info.items()
        },

        "ustatus": {
            name: capability_to_dict(value)
            for name, value in model.ustatus.items()
        },

        "variables": {
            name: capability_to_dict(value)
            for name, value in model.variables.items()
        },

        "print_controls": {
            name: capability_to_dict(value)
            for name, value in model.print_controls.items()
        },

        "physical": model.physical,
        "notes": model.notes,
    }


# ============================================================
# RELATORIO DE CAPACIDADES
# ============================================================


def print_capability_status(cap: Capability) -> None:
    if cap.status == STATUS_PHYSICAL_CONFIRMED:
        marker = "[OK]"
    elif cap.status == STATUS_JOB_CONFIRMED:
        marker = "[OK]"
    elif cap.status == STATUS_CONFIRMED:
        marker = "[OK]"
    elif cap.status == STATUS_QUERY_ONLY:
        marker = "[?]"
    elif cap.status == STATUS_UNSUPPORTED:
        marker = "[X]"
    else:
        marker = "[ ]"

    print(
        f"{marker} "
        f"{cap.name:18} "
        f"{cap.status}"
    )


def print_capability_report(
    model: CapabilityModel,
) -> None:

    print()
    print("=" * 72)
    print("CAPABILITY REPORT - MX611dhe")
    print("=" * 72)

    print()
    print("IDENTIDADE")
    print("-" * 72)

    print(
        f"[OK] Fabricante        : "
        f"{model.manufacturer}"
    )

    print(
        f"[OK] Modelo            : "
        f"{model.model}"
    )

    print(
        f"[OK] RAW               : "
        f"{model.raw_port}"
    )

    if "serial_number" in model.identity:
        print(
            f"[OK] Serial            : "
            f"{model.identity['serial_number']}"
        )

    if "system_firmware" in model.identity:
        print(
            f"[OK] System Firmware   : "
            f"{model.identity['system_firmware']}"
        )

    print()
    print("INFO PJL")
    print("-" * 72)

    for name, info in model.info.items():

        if info.supported and info.response:
            marker = "[OK]"
        elif info.supported:
            marker = "[?]"
        else:
            marker = "[X]"

        print(
            f"{marker} "
            f"{name:16} "
            f"{info.name}"
        )

    print()
    print("USTATUS")
    print("-" * 72)

    for cap in model.ustatus.values():
        print_capability_status(cap)

    print()
    print("VARIAVEIS PJL")
    print("-" * 72)

    for cap in model.variables.values():
        print_capability_status(cap)

    print()
    print("CONTROLES DE IMPRESSAO")
    print("-" * 72)

    for cap in model.print_controls.values():

        if cap.status == STATUS_PHYSICAL_CONFIRMED:
            marker = "[OK]"
        elif cap.status == STATUS_JOB_CONFIRMED:
            marker = "[OK]"
        elif cap.status == STATUS_CONFIRMED:
            marker = "[OK]"
        elif cap.status == STATUS_QUERY_ONLY:
            marker = "[?]"
        elif cap.status == STATUS_UNSUPPORTED:
            marker = "[X]"
        else:
            marker = "[ ]"

        print(
            f"{marker} "
            f"{cap.name:18} "
            f"{cap.status}"
        )

    print()
    print("CAPACIDADES FISICAS")
    print("-" * 72)

    for key, value in model.physical.items():
        print(
            f"{key:28} = {value}"
        )

    print()
    print("=" * 72)
    print("LEGENDA")
    print("=" * 72)

    print()
    print(
        "[OK] CONFIRMED           "
        "Comando/capacidade confirmada."
    )

    print(
        "[OK] JOB_CONFIRMED       "
        "Comportamento confirmado em job."
    )

    print(
        "[OK] PHYSICAL_CONFIRMED  "
        "Efeito fisico confirmado."
    )

    print(
        "[?]  QUERY_ONLY          "
        "Existe/responde, mas comportamento "
        "ainda nao foi confirmado."
    )

    print(
        "[X]  UNSUPPORTED         "
        "Testado e nao suportado."
    )

    print(
        "[ ]  UNKNOWN             "
        "Ainda nao investigado."
    )


# ============================================================
# CLI
# ============================================================


def main() -> None:

    model = build_mx611_capability_model()

    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 CAPABILITY MODEL")
    print("=" * 72)

    print()
    print(
        f"Fabricante : "
        f"{model.manufacturer}"
    )

    print(
        f"Modelo     : "
        f"{model.model}"
    )

    print(
        f"RAW        : "
        f"{model.raw_port}"
    )

    print()
    print("=" * 72)
    print("IDENTIDADE")
    print("=" * 72)

    for key, value in model.identity.items():
        print(
            f"{key:28} = {value}"
        )

    print()
    print("=" * 72)
    print("INFO PJL")
    print("=" * 72)

    for key, info in model.info.items():

        if info.supported:
            status = "[OK]"
        else:
            status = "[X]"

        response = (
            "RESPONDE"
            if info.response
            else "SEM RESPOSTA"
        )

        print(
            f"{status} "
            f"{key:12} "
            f"{response}"
        )

    print()
    print("=" * 72)
    print("USTATUS")
    print("=" * 72)

    for cap in model.ustatus.values():

        print(
            f"{cap.status:20} "
            f"{cap.name}"
        )

        if cap.values:
            print(
                f"    Valores: "
                f"{', '.join(cap.values)}"
            )

    print()
    print("=" * 72)
    print("VARIAVEIS PJL")
    print("=" * 72)

    for cap in model.variables.values():

        print()
        print(
            f"[{cap.name}]"
        )

        print(
            f"  status             = "
            f"{cap.status}"
        )

        print(
            f"  supported          = "
            f"{cap.supported}"
        )

        print(
            f"  SET confirmado     = "
            f"{cap.set_confirmed}"
        )

        print(
            f"  JOB confirmado     = "
            f"{cap.job_confirmed}"
        )

        print(
            f"  comportamento      = "
            f"{cap.behavior_confirmed}"
        )

        print(
            f"  RESET confirmado   = "
            f"{cap.reset_confirmed}"
        )

        print(
            f"  DEFAULT preservado = "
            f"{cap.default_preserved}"
        )

        if cap.values:
            print(
                f"  valores            = "
                f"{', '.join(cap.values)}"
            )

        if cap.notes:
            print(
                f"  observacao         = "
                f"{cap.notes}"
            )

    print()
    print("=" * 72)
    print("CONTROLES DE IMPRESSAO")
    print("=" * 72)

    for cap in model.print_controls.values():

        print_capability_status(cap)

    print()
    print("=" * 72)
    print("CAPACIDADES FISICAS")
    print("=" * 72)

    for key, value in model.physical.items():
        print(
            f"{key:28} = {value}"
        )

    print_capability_report(model)

    print()
    print("=" * 72)
    print("MODELO CONSTRUIDO")
    print("=" * 72)

    print()
    print(
        "[OK] Capability Model MX611 construido."
    )

    print(
        "[OK] Estados de capacidade consolidados."
    )

    print(
        "[OK] Conhecimento baseado nos probes realizados."
    )

    print(
        "[OK] Nenhuma comunicacao com a impressora foi executada."
    )

    print(
        "[OK] Nenhuma configuracao foi alterada."
    )


if __name__ == "__main__":
    main()