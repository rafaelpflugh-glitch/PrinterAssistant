"""
PRINTER ASSISTANT
MX611 OPERATION EXECUTOR

Executor de operações de alto nível.

Este módulo NÃO aceita PJL arbitrário.

A operação precisa existir no Operation Registry
e possuir mecanismo confirmado.

Operações atualmente liberadas:

    printer.config_page.print
    printer.demo_page.print

Operações LOCK continuam bloqueadas.

Nenhum reset, default, scanner ou firmware é executado
sem mecanismo confirmado.
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass

from ._operation_registry import (
    OperationDefinition,
    build_mx611_operation_registry,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

RAW_PORT = 9100

CONNECT_TIMEOUT = 5.0

READ_TIMEOUT = 3.0

RETRIES = 3


# ============================================================
# RESULTADO
# ============================================================


@dataclass
class OperationResult:

    success: bool

    operation: str

    mechanism: str = ""

    response: str = ""

    error: str = ""

    elapsed: float = 0.0


# ============================================================
# ERRO
# ============================================================


class OperationExecutionError(Exception):
    pass


# ============================================================
# EXECUTOR
# ============================================================


class OperationExecutor:

    def __init__(
        self,
        ip: str,
        port: int = RAW_PORT,
    ):

        self.ip = ip
        self.port = port

    # ========================================================
    # REGISTRY
    # ========================================================

    @staticmethod
    def get_operation(
        operation_name: str,
    ) -> OperationDefinition:

        registry = build_mx611_operation_registry()

        operation = registry.get(
            operation_name
        )

        if operation is None:

            raise OperationExecutionError(
                f"Operação inexistente: "
                f"{operation_name}"
            )

        if not operation.supported:

            raise OperationExecutionError(
                f"Operação não suportada: "
                f"{operation_name}"
            )

        if not operation.executable:

            raise OperationExecutionError(
                f"Operação ainda não suportada: "
                f"{operation_name}"
            )

        return operation

    # ========================================================
    # CONSTRUÇÃO DO COMANDO
    # ========================================================

    @staticmethod
    def build_command(
        operation: OperationDefinition,
    ) -> str:

        commands = {

            "printer.config_page.print":
                "@PJL LPRINTMENUS",

            "printer.demo_page.print":
                "@PJL LPRINTTESTPAGE",
        }

        command = commands.get(
            operation.name
        )

        if command is None:

            raise OperationExecutionError(
                (
                    "Nenhum comando operacional "
                    f"confirmado para "
                    f"{operation.name}"
                )
            )

        return command

    # ========================================================
    # CONFIRMAÇÃO
    # ========================================================

    @staticmethod
    def ask_confirmation(
        operation: OperationDefinition,
        command: str,
    ) -> bool:

        print()

        print("=" * 72)
        print("CONFIRMAÇÃO DE OPERAÇÃO")
        print("=" * 72)

        print()

        print(
            f"Operação  : {operation.name}"
        )

        print(
            f"Superfície: {operation.surface}"
        )

        print(
            f"Tipo      : {operation.operation_type}"
        )

        print(
            f"Alvo      : {operation.target}"
        )

        print()

        print(
            "Mecanismo confirmado:"
        )

        print(
            f"  {operation.mechanism}"
        )

        print()

        print(
            "Comando que será enviado:"
        )

        print(
            "------------------------------------------------------------------------"
        )

        print(
            command
        )

        print(
            "------------------------------------------------------------------------"
        )

        print()

        answer = input(
            "Executar na impressora? [S/N]: "
        ).strip().upper()

        return answer == "S"

    # ========================================================
    # ENVIO PJL
    # ========================================================

    def send_pjl(
        self,
        command: str,
    ) -> tuple[str, float]:

        payload = (
            "\x1b%-12345X"
            "@PJL\n"
            f"{command}\n"
            "\x1b%-12345X"
        )

        started = time.perf_counter()

        last_error = ""

        for attempt in range(
            1,
            RETRIES + 1,
        ):

            try:

                print(
                    f"Conectando em "
                    f"{self.ip}:{self.port} "
                    f"(tentativa "
                    f"{attempt}/{RETRIES})..."
                )

                with socket.create_connection(
                    (
                        self.ip,
                        self.port,
                    ),
                    timeout=CONNECT_TIMEOUT,
                ) as sock:

                    print(
                        "Conectado."
                    )

                    sock.settimeout(
                        READ_TIMEOUT
                    )

                    sock.sendall(
                        payload.encode(
                            "latin-1",
                            errors="replace",
                        )
                    )

                    chunks: list[bytes] = []

                    while True:

                        try:

                            data = sock.recv(
                                4096
                            )

                        except socket.timeout:

                            break

                        if not data:

                            break

                        chunks.append(
                            data
                        )

                response = (
                    b"".join(chunks)
                    .decode(
                        "latin-1",
                        errors="replace",
                    )
                )

                elapsed = (
                    time.perf_counter()
                    - started
                )

                return response, elapsed

            except OSError as exc:

                last_error = str(exc)

                print(
                    f"Falha: {exc}"
                )

                if attempt < RETRIES:

                    time.sleep(0.5)

        elapsed = (
            time.perf_counter()
            - started
        )

        raise OperationExecutionError(
            (
                "Falha ao comunicar com "
                f"{self.ip}:{self.port}: "
                f"{last_error}"
            )
        )

    # ========================================================
    # EXECUÇÃO
    # ========================================================

    def execute(
        self,
        operation_name: str,
        confirm: bool = True,
    ) -> OperationResult:

        started = time.perf_counter()

        try:

            operation = self.get_operation(
                operation_name
            )

            command = self.build_command(
                operation
            )

            if confirm:

                approved = self.ask_confirmation(
                    operation,
                    command,
                )

                if not approved:

                    return OperationResult(
                        success=False,
                        operation=operation_name,
                        mechanism=operation.mechanism,
                        error=(
                            "Operação cancelada "
                            "pelo operador."
                        ),
                        elapsed=(
                            time.perf_counter()
                            - started
                        ),
                    )

            print()

            print("=" * 72)
            print("EXECUTANDO OPERAÇÃO")
            print("=" * 72)

            print()

            print(
                f"Impressora : "
                f"{self.ip}:{self.port}"
            )

            print(
                f"Operação   : "
                f"{operation.name}"
            )

            print(
                f"Mecanismo  : "
                f"{operation.mechanism}"
            )

            print(
                f"Comando    : "
                f"{command}"
            )

            print()

            response, elapsed = self.send_pjl(
                command
            )

            print()

            print(
                "RESPOSTA"
            )

            print(
                "------------------------------------------------------------------------"
            )

            if response:

                print(
                    response
                )

            else:

                print(
                    "(sem resposta)"
                )

            print(
                "------------------------------------------------------------------------"
            )

            print()

            print(
                f"Tempo: {elapsed:.3f}s"
            )

            return OperationResult(
                success=True,
                operation=operation_name,
                mechanism=operation.mechanism,
                response=response,
                elapsed=elapsed,
            )

        except OperationExecutionError as exc:

            elapsed = (
                time.perf_counter()
                - started
            )

            print()

            print(
                f"✗ ERRO: {exc}"
            )

            return OperationResult(
                success=False,
                operation=operation_name,
                error=str(exc),
                elapsed=elapsed,
            )

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - started
            )

            print()

            print(
                f"✗ ERRO INESPERADO: {exc}"
            )

            return OperationResult(
                success=False,
                operation=operation_name,
                error=str(exc),
                elapsed=elapsed,
            )


# ============================================================
# INTERFACE CLI
# ============================================================


def main() -> None:

    print("=" * 72)

    print(
        "PRINTER ASSISTANT - MX611 OPERATION EXECUTOR"
    )

    print("=" * 72)

    print()

    print(
        "Este executor trabalha somente com "
        "operações registradas."
    )

    print(
        "Somente operações EXEC podem ser executadas."
    )

    print(
        "Operações LOCK permanecem bloqueadas."
    )

    print(
        "Nenhum comando PJL arbitrário será aceito."
    )

    print()

    ip = input(
        "Digite o IP da impressora: "
    ).strip()

    if not ip:

        print(
            "IP inválido."
        )

        return

    print()

    print(
        f"Impressora: {ip}"
    )

    print()

    registry = (
        build_mx611_operation_registry()
    )

    print(
        "OPERAÇÕES REGISTRADAS:"
    )

    print()

    for operation in registry.values():

        if (
            operation.supported
            and operation.executable
        ):

            status = "EXEC"

        elif operation.supported:

            status = "LOCK"

        else:

            status = "X"

        print(
            f"  [{status}] "
            f"{operation.name}"
        )

    print()

    operation_name = input(
        "Digite a operação: "
    ).strip()

    executor = OperationExecutor(
        ip=ip
    )

    result = executor.execute(
        operation_name=operation_name,
        confirm=True,
    )

    print()

    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    print()

    if result.success:

        print(
            "✓ OPERAÇÃO EXECUTADA."
        )

        print(
            f"Operação : {result.operation}"
        )

        print(
            f"Mecanismo: {result.mechanism}"
        )

        print(
            f"Tempo    : {result.elapsed:.3f}s"
        )

    else:

        print(
            "✗ OPERAÇÃO NÃO EXECUTADA."
        )

        if result.error:

            print(
                f"Motivo: {result.error}"
            )

    print()

    print("=" * 72)


if __name__ == "__main__":

    main()