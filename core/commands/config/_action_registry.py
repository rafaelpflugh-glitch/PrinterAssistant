"""
PRINTER ASSISTANT
MX611 ACTION REGISTRY

Registro central da superfície operacional conhecida
da Lexmark MX611dhe.

IMPORTANTE:

Este módulo NÃO executa comandos.

Ele apenas declara quais ações existem e qual é
o estado operacional de cada uma.

Estados:

[EXEC] = ação conhecida e liberada para executor
[LOCK] = ação conhecida, mas ainda bloqueada
[X]    = ação não suportada / não implementada
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# TIPOS
# ============================================================

SURFACE_PJL = "PJL"
SURFACE_EWS = "EWS"
SURFACE_SYSTEM = "SYSTEM"


TYPE_QUERY = "QUERY"
TYPE_SET = "SET"
TYPE_RESET = "RESET"
TYPE_DEFAULT = "DEFAULT"
TYPE_EWS = "EWS"
TYPE_SYSTEM = "SYSTEM"


STATUS_EXEC = "EXEC"
STATUS_LOCK = "LOCK"
STATUS_UNSUPPORTED = "X"


# ============================================================
# ACTION
# ============================================================


@dataclass(frozen=True)
class Action:
    name: str
    surface: str
    action_type: str
    target: str
    status: str

    description: str = ""

    # Indica que a ação já possui evidência suficiente
    # para ser liberada operacionalmente.
    confirmed: bool = False


# ============================================================
# REGISTRY
# ============================================================


def build_mx611_action_registry() -> dict[str, Action]:
    """
    Constrói o registro operacional da MX611dhe.

    Este método NÃO conversa com a impressora.
    """

    actions: dict[str, Action] = {

        # ====================================================
        # CONSULTAS PJL
        # ====================================================

        "query.status": Action(
            name="query.status",
            surface=SURFACE_PJL,
            action_type=TYPE_QUERY,
            target="INFO STATUS",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Consulta estado atual da impressora."
            ),
        ),

        "query.variables": Action(
            name="query.variables",
            surface=SURFACE_PJL,
            action_type=TYPE_QUERY,
            target="INFO VARIABLES",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Consulta variáveis PJL conhecidas."
            ),
        ),

        "query.config": Action(
            name="query.config",
            surface=SURFACE_PJL,
            action_type=TYPE_QUERY,
            target="INFO CONFIG",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Consulta configuração física e capacidades."
            ),
        ),

        # ====================================================
        # PAPER
        # ====================================================

        "paper.set": Action(
            name="paper.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="PAPER",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera PAPER.",
        ),

        "paper.reset": Action(
            name="paper.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="PAPER",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a PAPER.",
        ),

        # ====================================================
        # MEDIATYPE
        # ====================================================

        "mediatype.set": Action(
            name="mediatype.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="MEDIATYPE",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera MEDIATYPE.",
        ),

        "mediatype.reset": Action(
            name="mediatype.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="MEDIATYPE",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a MEDIATYPE.",
        ),

        # ====================================================
        # DUPLEX
        # ====================================================

        "duplex.set": Action(
            name="duplex.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="DUPLEX",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera DUPLEX.",
        ),

        "duplex.reset": Action(
            name="duplex.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="DUPLEX",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a DUPLEX.",
        ),

        # ====================================================
        # COPIES
        # ====================================================

        "copies.set": Action(
            name="copies.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="COPIES",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera número de cópias.",
        ),

        "copies.reset": Action(
            name="copies.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="COPIES",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a COPIES.",
        ),

        # ====================================================
        # RESOLUTION
        # ====================================================

        "resolution.set": Action(
            name="resolution.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="RESOLUTION",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera resolução do job.",
        ),

        "resolution.reset": Action(
            name="resolution.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="RESOLUTION",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a RESOLUTION.",
        ),

        # ====================================================
        # DENSITY
        # ====================================================

        "density.set": Action(
            name="density.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="DENSITY",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera densidade.",
        ),

        "density.reset": Action(
            name="density.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="DENSITY",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a DENSITY.",
        ),

        # ====================================================
        # ORIENTATION
        # ====================================================

        "orientation.set": Action(
            name="orientation.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="ORIENTATION",
            status=STATUS_EXEC,
            confirmed=True,
            description="Altera orientação do job.",
        ),

        "orientation.reset": Action(
            name="orientation.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="ORIENTATION",
            status=STATUS_EXEC,
            confirmed=True,
            description="Executa RESET relacionado a ORIENTATION.",
        ),

        # ====================================================
        # ECONOMODE
        # ====================================================

        "economode.set": Action(
            name="economode.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="ECONOMODE",
            status=STATUS_LOCK,
            confirmed=False,
            description=(
                "SET ECONOMODE existe no ambiente PJL, "
                "mas ainda não foi confirmado por INQUIRE."
            ),
        ),

        "economode.reset": Action(
            name="economode.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="ECONOMODE",
            status=STATUS_LOCK,
            confirmed=False,
            description=(
                "RESET foi enviado durante probe, "
                "mas ECONOMODE ainda não está liberado "
                "como capacidade operacional."
            ),
        ),

        # ====================================================
        # LANGUAGE
        # ====================================================

        "language.set": Action(
            name="language.set",
            surface=SURFACE_PJL,
            action_type=TYPE_SET,
            target="LANG",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Altera o idioma da interface da impressora "
                "através da variável LANG."
            ),
        ),

        "language.reset": Action(
            name="language.reset",
            surface=SURFACE_PJL,
            action_type=TYPE_RESET,
            target="LANG",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Restaura o ambiente corrente relacionado "
                "à linguagem através de RESET."
            ),
        ),

        # ====================================================
        # EWS
        # ====================================================

        "ews.home": Action(
            name="ews.home",
            surface=SURFACE_EWS,
            action_type=TYPE_EWS,
            target="/",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Acessa a interface web da impressora."
            ),
        ),

        "ews.language": Action(
            name="ews.language",
            surface=SURFACE_EWS,
            action_type=TYPE_EWS,
            target="/cgi-bin/dynamic/printer/langbar.html",
            status=STATUS_LOCK,
            confirmed=False,
            description=(
                "Superfície EWS de seleção de idioma "
                "identificada, mas mecanismo de alteração "
                "ainda não foi implementado."
            ),
        ),

        # ====================================================
        # FIRMWARE
        # ====================================================

        "firmware.system.query": Action(
            name="firmware.system.query",
            surface=SURFACE_SYSTEM,
            action_type=TYPE_QUERY,
            target="SYSTEM FIRMWARE VERSION",
            status=STATUS_EXEC,
            confirmed=True,
            description=(
                "Consulta versão do firmware do sistema."
            ),
        ),

        "firmware.update": Action(
            name="firmware.update",
            surface=SURFACE_SYSTEM,
            action_type=TYPE_SYSTEM,
            target="FIRMWARE",
            status=STATUS_UNSUPPORTED,
            confirmed=False,
            description=(
                "Atualização de firmware ainda não possui "
                "mecanismo operacional confirmado."
            ),
        ),
    }

    return actions


# ============================================================
# FUNÇÕES DE CONSULTA
# ============================================================


def get_action(name: str) -> Action | None:
    """
    Retorna uma ação pelo nome.
    """

    registry = build_mx611_action_registry()
    return registry.get(name)


def get_executable_actions() -> dict[str, Action]:
    """
    Retorna somente ações liberadas para execução.
    """

    registry = build_mx611_action_registry()

    return {
        name: action
        for name, action in registry.items()
        if action.status == STATUS_EXEC
    }


def get_locked_actions() -> dict[str, Action]:
    """
    Retorna ações conhecidas mas bloqueadas.
    """

    registry = build_mx611_action_registry()

    return {
        name: action
        for name, action in registry.items()
        if action.status == STATUS_LOCK
    }


# ============================================================
# RELATÓRIO
# ============================================================


def print_registry() -> None:

    registry = build_mx611_action_registry()

    print("=" * 80)
    print("PRINTER ASSISTANT - MX611 ACTION REGISTRY")
    print("=" * 80)

    print()
    print(
        "Este módulo NÃO executa comandos."
    )

    print(
        "Ele apenas registra a superfície operacional conhecida."
    )

    print()
    print("=" * 80)
    print("ACTION REGISTRY - MX611dhe")
    print("=" * 80)

    print()
    print("Fabricante : Lexmark")
    print("Modelo     : MX611dhe")

    print()
    print("-" * 80)
    print(
        f"{'STATUS':8} "
        f"{'AÇÃO':28} "
        f"{'SUPERF.':8} "
        f"{'TIPO':8} "
        f"ALVO"
    )
    print("-" * 80)

    for action in registry.values():

        print(
            f"[{action.status:4}] "
            f"{action.name:28} "
            f"{action.surface:8} "
            f"{action.action_type:8} "
            f"{action.target}"
        )

    executable = get_executable_actions()
    locked = get_locked_actions()

    print()
    print("-" * 80)

    print(
        f"Ações conhecidas : {len(registry)}"
    )

    print(
        f"Ações executáveis: {len(executable)}"
    )

    print(
        f"Ações bloqueadas : {len(locked)}"
    )

    print()
    print(
        "[EXEC] = suportada e liberada para executor"
    )

    print(
        "[LOCK] = conhecida, mas ainda bloqueada"
    )

    print(
        "[X]    = não suportada"
    )

    print()
    print("=" * 80)
    print("VALIDAÇÃO")
    print("=" * 80)

    errors = 0

    # --------------------------------------------------------
    # AÇÕES QUE DEVEM ESTAR EXEC
    # --------------------------------------------------------

    required_exec = [
        "query.status",
        "query.variables",
        "query.config",

        "paper.set",
        "paper.reset",

        "mediatype.set",
        "mediatype.reset",

        "duplex.set",
        "duplex.reset",

        "copies.set",
        "copies.reset",

        "resolution.set",
        "resolution.reset",

        "density.set",
        "density.reset",

        "orientation.set",
        "orientation.reset",

        "language.set",
        "language.reset",

        "ews.home",

        "firmware.system.query",
    ]

    for name in required_exec:

        action = registry.get(name)

        if action is None:
            print(
                f"✗ {name}: ação ausente."
            )
            errors += 1
            continue

        if action.status != STATUS_EXEC:
            print(
                f"✗ {name}: deveria estar EXEC."
            )
            errors += 1
        else:
            print(
                f"✓ {name}: EXEC."
            )

    # --------------------------------------------------------
    # AÇÕES QUE DEVEM CONTINUAR LOCK
    # --------------------------------------------------------

    required_lock = [
        "economode.set",
        "economode.reset",
        "ews.language",
    ]

    for name in required_lock:

        action = registry.get(name)

        if action is None:
            print(
                f"✗ {name}: ação ausente."
            )
            errors += 1
            continue

        if action.status != STATUS_LOCK:
            print(
                f"✗ {name}: deveria continuar LOCK."
            )
            errors += 1
        else:
            print(
                f"✓ {name}: LOCK."
            )

    # --------------------------------------------------------
    # FIRMWARE
    # --------------------------------------------------------

    firmware = registry.get("firmware.update")

    if firmware is None:
        print(
            "✗ firmware.update: ação ausente."
        )
        errors += 1

    elif firmware.status != STATUS_UNSUPPORTED:
        print(
            "✗ firmware.update: classificação incorreta."
        )
        errors += 1

    else:
        print(
            "✓ firmware.update: não suportado."
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print()
    print("=" * 80)

    if errors == 0:
        print("✓ ACTION REGISTRY VALIDADO.")
        print(
            "✓ Ações confirmadas separadas das ações ainda bloqueadas."
        )
        print(
            "✓ LANGUAGE foi promovida para ação operacional."
        )
    else:
        print(
            f"✗ Foram encontrados {errors} problemas."
        )

    print("=" * 80)


# ============================================================
# CLI
# ============================================================


def main() -> None:
    print_registry()


if __name__ == "__main__":
    main()