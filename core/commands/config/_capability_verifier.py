"""
PRINTER ASSISTANT
MX611 CAPABILITY VERIFIER

Verifica se o Capability Model interno está
coerente com os resultados conhecidos da MX611dhe.

Este arquivo NÃO conversa com a impressora.
"""

from __future__ import annotations

from ._capability_model import (
    build_mx611_capability_model,
)


def check(condition: bool, ok: str, fail: str) -> bool:
    if condition:
        print(f"✓ {ok}")
        return True

    print(f"✗ {fail}")
    return False


def main() -> None:

    print("=" * 72)
    print("PRINTER ASSISTANT - MX611 CAPABILITY VERIFIER")
    print("=" * 72)

    model = build_mx611_capability_model()

    errors = 0

    print()
    print(f"Modelo interno: {model.manufacturer} {model.model}")

    # ========================================================
    # IDENTIDADE
    # ========================================================

    print()

    if not check(
        model.manufacturer == "Lexmark",
        "FABRICANTE: Lexmark OK.",
        "FABRICANTE: inconsistente.",
    ):
        errors += 1

    if not check(
        model.model == "MX611dhe",
        "MODELO: MX611dhe OK.",
        "MODELO: inconsistente.",
    ):
        errors += 1

    # ========================================================
    # INFO
    # ========================================================

    required_info = [
        "ID",
        "STATUS",
        "PAGECOUNT",
        "MEMORY",
        "VARIABLES",
        "USTATUS",
        "CONFIG",
    ]

    for name in required_info:

        info = model.info.get(name)

        if not check(
            info is not None and info.supported and info.response,
            f"INFO {name}: OK.",
            f"INFO {name}: inconsistente.",
        ):
            errors += 1

    # ========================================================
    # INFO QUE NÃO RESPONDE
    # ========================================================

    for name in ["PRODINFO", "FILESYS"]:

        info = model.info.get(name)

        if not check(
            info is not None and not info.supported,
            f"INFO {name}: corretamente marcado como não suportado.",
            f"INFO {name}: classificação incorreta.",
        ):
            errors += 1

    # ========================================================
    # USTATUS
    # ========================================================

    for name in ["DEVICE", "JOB", "PAGE", "TIMED"]:

        cap = model.ustatus.get(name)

        if not check(
            cap is not None and cap.supported,
            f"USTATUS {name}: OK.",
            f"USTATUS {name}: ausente ou inconsistente.",
        ):
            errors += 1

    # ========================================================
    # CONTROLES CRÍTICOS
    # ========================================================

    # PAPER
    paper = model.variables["PAPER"]

    if not check(
        paper.supported
        and paper.set_confirmed
        and paper.reset_confirmed,
        "PAPER: SET/RESET confirmado.",
        "PAPER: modelo inconsistente.",
    ):
        errors += 1

    # MEDIATYPE
    mediatype = model.variables["MEDIATYPE"]

    if not check(
        mediatype.supported
        and mediatype.set_confirmed
        and mediatype.reset_confirmed,
        "MEDIATYPE: SET/RESET confirmado.",
        "MEDIATYPE: modelo inconsistente.",
    ):
        errors += 1

    # DUPLEX
    duplex = model.variables["DUPLEX"]

    if not check(
        duplex.supported
        and duplex.set_confirmed
        and duplex.behavior_confirmed
        and duplex.reset_confirmed,
        "DUPLEX: comportamento físico confirmado.",
        "DUPLEX: modelo inconsistente.",
    ):
        errors += 1

    # COPIES
    copies = model.variables["COPIES"]

    if not check(
        copies.supported
        and copies.set_confirmed
        and copies.behavior_confirmed
        and copies.reset_confirmed,
        "COPIES: comportamento confirmado.",
        "COPIES: modelo inconsistente.",
    ):
        errors += 1

    # RESOLUTION
    resolution = model.variables["RESOLUTION"]

    if not check(
        resolution.supported
        and resolution.behavior_confirmed
        and resolution.reset_confirmed,
        "RESOLUTION: efeito físico confirmado.",
        "RESOLUTION: modelo inconsistente.",
    ):
        errors += 1

    # DENSITY
    density = model.variables["DENSITY"]

    if not check(
        density.supported
        and density.behavior_confirmed
        and density.reset_confirmed,
        "DENSITY: efeito físico confirmado.",
        "DENSITY: modelo inconsistente.",
    ):
        errors += 1

    # ORIENTATION
    orientation = model.variables["ORIENTATION"]

    if not check(
        orientation.supported
        and orientation.behavior_confirmed
        and orientation.reset_confirmed,
        "ORIENTATION: efeito físico confirmado.",
        "ORIENTATION: modelo consistente.",
    ):
        errors += 1

    # ========================================================
    # DEFAULT
    # ========================================================

    for name, cap in model.variables.items():

        if cap.set_confirmed or cap.behavior_confirmed:

            if not check(
                cap.default_preserved,
                f"{name}: DEFAULT preservado.",
                f"{name}: DEFAULT marcado incorretamente.",
            ):
                errors += 1

    # ========================================================
    # RESULTADO
    # ========================================================

    print()
    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    if errors == 0:
        print()
        print("✓ CAPABILITY MODEL VALIDADO.")
        print()
        print(
            "O modelo interno da MX611dhe está coerente "
            "com os probes realizados."
        )
    else:
        print()
        print(f"✗ Foram encontrados {errors} problemas no modelo.")

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()