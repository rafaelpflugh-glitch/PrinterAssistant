"""
PRINTER ASSISTANT
MX611 OPERATION REGISTRY

Registro das operações de alto nível que o Printer Assistant
pode executar na MX611.

IMPORTANTE:

Uma operação somente deve ser marcada como EXEC quando:

1. o mecanismo foi identificado;
2. o mecanismo foi testado;
3. o efeito produzido corresponde ao objetivo da operação.

Um comando aceito pela impressora NÃO significa automaticamente
que a operação foi realizada corretamente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


# ============================================================
# TIPOS
# ============================================================

OP_PRINT = "PRINT"
OP_ENABLE_DISABLE = "ENABLE_DISABLE"
OP_RESET = "RESET"
OP_DEFAULT = "DEFAULT"


SURFACE_PJL = "PJL"
SURFACE_EWS = "EWS"


# ============================================================
# DEFINIÇÃO
# ============================================================


@dataclass(frozen=True)
class OperationDefinition:

    name: str

    surface: str

    operation_type: str

    target: str

    supported: bool

    executable: bool

    mechanism: str = ""

    description: str = ""

    expected_result: str = ""

    validation: str = ""


# ============================================================
# REGISTRY MX611
# ============================================================


def build_mx611_operation_registry() -> Dict[str, OperationDefinition]:

    return {

        # ----------------------------------------------------
        # CONFIGURATION PAGE
        # ----------------------------------------------------

        "printer.config_page.print": OperationDefinition(

            name="printer.config_page.print",

            surface=SURFACE_PJL,

            operation_type=OP_PRINT,

            target="CONFIGURATION PAGE",

            supported=True,

            executable=True,

            mechanism="@PJL LPRINTMENUS",

            description=(
                "Imprime a Menu Settings Page da impressora."
            ),

            expected_result=(
                "Uma página contendo as configurações "
                "da impressora deve ser impressa."
            ),

            validation=(
                "Confirmado fisicamente na MX611dhe."
            ),
        ),

        # ----------------------------------------------------
        # DEMO PAGE
        # ----------------------------------------------------

        "printer.demo_page.print": OperationDefinition(

            name="printer.demo_page.print",

            surface=SURFACE_PJL,

            operation_type=OP_PRINT,

            target="DEMONSTRATION PAGE",

            supported=True,

            executable=False,

            mechanism="@PJL LPRINTTESTPAGE",

            description=(
                "Comando identificado como mecanismo candidato "
                "para a página interna de demonstração."
            ),

            expected_result=(
                "Uma página de demonstração distinta da "
                "Menu Settings Page deve ser impressa."
            ),

            validation=(
                "NÃO confirmado. Na MX611dhe testada, "
                "@PJL LPRINTTESTPAGE imprimiu novamente "
                "a Menu Settings Page."
            ),
        ),

        # ----------------------------------------------------
        # ASSET REPORT
        # ----------------------------------------------------

        "printer.asset_report.print": OperationDefinition(

            name="printer.asset_report.print",

            surface=SURFACE_PJL,

            operation_type=OP_PRINT,

            target="ASSET REPORT",

            supported=True,

            executable=False,

            description=(
                "Imprime o relatório de ativo da impressora."
            ),

            expected_result=(
                "Uma página contendo as informações "
                "de ativo da impressora deve ser impressa."
            ),

            validation=(
                "Mecanismo ainda não confirmado."
            ),
        ),

        # ----------------------------------------------------
        # SCANNER ENABLE
        # ----------------------------------------------------

        "scanner.enable": OperationDefinition(

            name="scanner.enable",

            surface=SURFACE_EWS,

            operation_type=OP_ENABLE_DISABLE,

            target="SCANNER",

            supported=True,

            executable=False,

            description=(
                "Ativa o scanner da multifuncional."
            ),

            expected_result=(
                "Scanner habilitado."
            ),

            validation=(
                "Mecanismo EWS ainda não confirmado."
            ),
        ),

        # ----------------------------------------------------
        # SCANNER DISABLE
        # ----------------------------------------------------

        "scanner.disable": OperationDefinition(

            name="scanner.disable",

            surface=SURFACE_EWS,

            operation_type=OP_ENABLE_DISABLE,

            target="SCANNER",

            supported=True,

            executable=False,

            description=(
                "Desativa o scanner da multifuncional."
            ),

            expected_result=(
                "Scanner desabilitado."
            ),

            validation=(
                "Mecanismo EWS ainda não confirmado."
            ),
        ),

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------

        "printer.reset": OperationDefinition(

            name="printer.reset",

            surface=SURFACE_PJL,

            operation_type=OP_RESET,

            target="PRINTER",

            supported=True,

            executable=False,

            description=(
                "Executa reset controlado da impressora."
            ),

            expected_result=(
                "Impressora reiniciada/resetada conforme "
                "o mecanismo definido."
            ),

            validation=(
                "Mecanismo ainda não confirmado."
            ),
        ),

        # ----------------------------------------------------
        # DEFAULTS
        # ----------------------------------------------------

        "printer.defaults": OperationDefinition(

            name="printer.defaults",

            surface=SURFACE_PJL,

            operation_type=OP_DEFAULT,

            target="PRINTER",

            supported=True,

            executable=False,

            description=(
                "Restaura as configurações padrão da impressora."
            ),

            expected_result=(
                "Configurações restauradas para os padrões "
                "correspondentes ao mecanismo utilizado."
            ),

            validation=(
                "Mecanismo ainda não confirmado."
            ),
        ),
    }


# ============================================================
# IMPRESSÃO DO REGISTRY
# ============================================================


def print_registry() -> None:

    registry = build_mx611_operation_registry()

    print("=" * 80)
    print("PRINTER ASSISTANT - MX611 OPERATION REGISTRY")
    print("=" * 80)

    print()

    print(
        "Este módulo NÃO executa operações."
    )

    print(
        "Ele apenas registra a superfície operacional conhecida."
    )

    print()

    print("=" * 80)
    print("OPERATION REGISTRY - MX611dhe")
    print("=" * 80)

    print()

    print("Fabricante : Lexmark")
    print("Modelo     : MX611dhe")

    print()

    print("-" * 80)

    print(
        f"{'STATUS':<8}"
        f"{'OPERAÇÃO':<35}"
        f"{'SUPERF.':<9}"
        f"{'TIPO':<16}"
        f"{'ALVO'}"
    )

    print("-" * 80)

    for operation in registry.values():

        if (
            operation.supported
            and operation.executable
        ):

            status = "[EXEC]"

        elif operation.supported:

            status = "[LOCK]"

        else:

            status = "[X]"

        print(
            f"{status:<8}"
            f"{operation.name:<35}"
            f"{operation.surface:<9}"
            f"{operation.operation_type:<16}"
            f"{operation.target}"
        )

    print("-" * 80)

    total = len(registry)

    executable = sum(
        1
        for op in registry.values()
        if op.supported and op.executable
    )

    locked = sum(
        1
        for op in registry.values()
        if op.supported and not op.executable
    )

    unsupported = sum(
        1
        for op in registry.values()
        if not op.supported
    )

    print()

    print(
        f"Operações conhecidas : {total}"
    )

    print(
        f"Operações executáveis: {executable}"
    )

    print(
        f"Operações bloqueadas : {locked}"
    )

    print(
        f"Não suportadas       : {unsupported}"
    )

    print()

    print(
        "[EXEC] = mecanismo confirmado e liberado"
    )

    print(
        "[LOCK] = operação conhecida, mecanismo/efeito "
        "ainda não confirmado"
    )

    print(
        "[X]    = operação não suportada"
    )

    print()

    print("=" * 80)
    print("MECANISMOS CONFIRMADOS")
    print("=" * 80)

    print()

    for operation in registry.values():

        if (
            operation.supported
            and operation.executable
        ):

            print(
                f"✓ {operation.name}"
            )

            print(
                f"  superfície : {operation.surface}"
            )

            print(
                f"  mecanismo  : {operation.mechanism}"
            )

            print(
                f"  descrição  : {operation.description}"
            )

            print(
                f"  resultado  : {operation.expected_result}"
            )

            print(
                f"  validação  : {operation.validation}"
            )

            print()

    print("=" * 80)
    print("OPERAÇÕES BLOQUEADAS")
    print("=" * 80)

    print()

    for operation in registry.values():

        if (
            operation.supported
            and not operation.executable
        ):

            print(
                f"• {operation.name}"
            )

            print(
                f"  alvo       : {operation.target}"
            )

            if operation.mechanism:

                print(
                    f"  candidato  : {operation.mechanism}"
                )

            print(
                f"  esperado   : {operation.expected_result}"
            )

            print(
                f"  situação   : {operation.validation}"
            )

            print()

    print("=" * 80)
    print("VALIDAÇÃO")
    print("=" * 80)

    print()

    for operation in registry.values():

        if not operation.supported:

            status = "NÃO SUPORTADA"

        elif operation.executable:

            status = "EXEC"

        else:

            status = "LOCK"

        print(
            f"✓ {operation.name}: {status}."
        )

    print()

    print(
        "✓ OPERATION REGISTRY VALIDADO."
    )

    print()

    print("=" * 80)
    print("FIM")
    print("=" * 80)


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    print_registry()