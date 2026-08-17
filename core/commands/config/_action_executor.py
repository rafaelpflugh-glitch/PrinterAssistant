"""
PRINTER ASSISTANT
MX611 ACTION EXECUTOR

Executor controlado das ações registradas no Action Registry.

Este módulo é o primeiro ponto em que o PrinterAssistant
pode efetivamente executar uma ação PJL na impressora.

REGRAS:

1. A ação precisa existir no Action Registry.
2. A ação precisa estar marcada como supported=True.
3. A ação precisa estar marcada como executable=True.
4. Valores precisam estar dentro dos valores permitidos.
5. Ação SET exige confirmação explícita do operador.
6. Nenhum RESET automático é executado.
7. Nenhum DEFAULT automático é executado.
8. Nenhum JOB é enviado por este módulo.
9. O executor não aceita comandos PJL arbitrários.
10. O executor não executa ações LOCKED.

Arquitetura:

    Action Registry
          |
          v
    Action Executor
          |
          v
       PJL RAW
          |
          v
       MX611
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Optional

from ._action_registry import (
    ACTION_QUERY,
    ACTION_SET,
    ActionDefinition,
    build_mx611_action_registry,
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
class ActionResult:

    success: bool

    action: str

    command: str

    response: str = ""

    error: str = ""

    elapsed: float = 0.0


# ============================================================
# ERROS
# ============================================================


class ActionExecutionError(Exception):
    pass


# ============================================================
# EXECUTOR
# ============================================================


class ActionExecutor:

    def __init__(
        self,
        ip: str,
        port: int = RAW_PORT,
    ):

        self.ip = ip
        self.port = port

    # ========================================================
    # VALIDAÇÃO DA AÇÃO
    # ========================================================

    def get_action(
        self,
        action_name: str,
    ) -> ActionDefinition:

        registry = build_mx611_action_registry()

        action = registry.get(action_name)

        if action is None:

            raise ActionExecutionError(
                f"Ação inexistente: {action_name}"
            )

        if not action.supported:

            raise ActionExecutionError(
                f"Ação não suportada: {action_name}"
            )

        if not action.executable:

            raise ActionExecutionError(
                f"Ação bloqueada: {action_name}"
            )

        return action

    # ========================================================
    # VALIDAÇÃO DO VALOR
    # ========================================================

    def validate_value(
        self,
        action: ActionDefinition,
        value: Optional[str],
    ) -> None:

        if action.action_type != ACTION_SET:
            return

        if value is None:
            raise ActionExecutionError(
                f"A ação {action.name} exige um valor."
            )

        value = str(value).upper()

        # ----------------------------------------------------
        # Faixas numéricas
        # ----------------------------------------------------

        if action.values == ["1-999"]:

            try:
                number = int(value)
            except ValueError:

                raise ActionExecutionError(
                    "COPIES deve ser um número entre 1 e 999."
                )

            if not 1 <= number <= 999:

                raise ActionExecutionError(
                    "COPIES deve estar entre 1 e 999."
                )

            return

        # ----------------------------------------------------

        if action.values == ["1", "2", "3", "4", "5"]:

            if value not in action.values:

                raise ActionExecutionError(
                    "DENSITY deve estar entre 1 e 5."
                )

            return

        # ----------------------------------------------------

        if action.values == ["600", "1200"]:

            if value not in action.values:

                raise ActionExecutionError(
                    "RESOLUTION deve ser 600 ou 1200."
                )

            return

        # ----------------------------------------------------
        # Valores enumerados
        # ----------------------------------------------------

        if action.values:

            if value not in action.values:

                raise ActionExecutionError(
                    (
                        f"Valor inválido para "
                        f"{action.target}: {value}"
                    )
                )

    # ========================================================
    # MONTAGEM DO COMANDO
    # ========================================================

    def build_command(
        self,
        action: ActionDefinition,
        value: Optional[str] = None,
    ) -> str:

        self.validate_value(
            action,
            value,
        )

        if not action.command_template:

            raise ActionExecutionError(
                f"Ação {action.name} não possui "
                "command_template."
            )

        if "{value}" in action.command_template:

            if value is None:

                raise ActionExecutionError(
                    f"Ação {action.name} exige valor."
                )

            return action.command_template.format(
                value=str(value).upper()
            )

        return action.command_template

    # ========================================================
    # CONEXÃO RAW
    # ========================================================

    def send_raw(
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

                            data = sock.recv(4096)

                        except socket.timeout:

                            break

                        if not data:
                            break

                        chunks.append(
                            data
                        )

                response_bytes = b"".join(
                    chunks
                )

                response = response_bytes.decode(
                    "latin-1",
                    errors="replace",
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

        raise ActionExecutionError(
            (
                f"Falha ao comunicar com "
                f"{self.ip}:{self.port}: "
                f"{last_error}"
            )
        )

    # ========================================================
    # CONFIRMAÇÃO
    # ========================================================

    @staticmethod
    def ask_confirmation(
        action: ActionDefinition,
        command: str,
    ) -> bool:

        print()
        print("=" * 72)
        print("CONFIRMAÇÃO DE AÇÃO")
        print("=" * 72)

        print()

        print(
            f"Ação     : {action.name}"
        )

        print(
            f"Superfície: {action.surface}"
        )

        print(
            f"Tipo     : {action.action_type}"
        )

        print(
            f"Alvo     : {action.target}"
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
    # EXECUÇÃO
    # ========================================================

    def execute(
        self,
        action_name: str,
        value: Optional[str] = None,
        confirm: bool = True,
    ) -> ActionResult:

        started = time.perf_counter()

        try:

            # ------------------------------------------------
            # Buscar ação
            # ------------------------------------------------

            action = self.get_action(
                action_name
            )

            # ------------------------------------------------
            # Montar comando
            # ------------------------------------------------

            command = self.build_command(
                action,
                value,
            )

            # ------------------------------------------------
            # Confirmação
            # ------------------------------------------------

            if confirm:

                approved = self.ask_confirmation(
                    action,
                    command,
                )

                if not approved:

                    return ActionResult(
                        success=False,
                        action=action_name,
                        command=command,
                        error="Operação cancelada pelo operador.",
                        elapsed=(
                            time.perf_counter()
                            - started
                        ),
                    )

            # ------------------------------------------------
            # Executar
            # ------------------------------------------------

            print()
            print(
                "=" * 72
            )

            print(
                "EXECUTANDO AÇÃO"
            )

            print(
                "=" * 72
            )

            print()

            print(
                f"Impressora : "
                f"{self.ip}:{self.port}"
            )

            print(
                f"Ação       : "
                f"{action.name}"
            )

            print(
                f"Comando    : "
                f"{command}"
            )

            print()

            response, elapsed = self.send_raw(
                command
            )

            # ------------------------------------------------
            # Resultado
            # ------------------------------------------------

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

            return ActionResult(
                success=True,
                action=action_name,
                command=command,
                response=response,
                elapsed=elapsed,
            )

        except ActionExecutionError as exc:

            elapsed = (
                time.perf_counter()
                - started
            )

            print()
            print(
                f"✗ ERRO: {exc}"
            )

            return ActionResult(
                success=False,
                action=action_name,
                command="",
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

            return ActionResult(
                success=False,
                action=action_name,
                command="",
                error=str(exc),
                elapsed=elapsed,
            )


# ============================================================
# TESTE CONTROLADO
# ============================================================


def main() -> None:

    print("=" * 72)
    print(
        "PRINTER ASSISTANT - MX611 ACTION EXECUTOR"
    )
    print("=" * 72)

    print()

    print(
        "ATENÇÃO:"
    )

    print(
        "Este programa pode enviar comandos para a impressora."
    )

    print(
        "Somente ações marcadas como EXEC podem ser executadas."
    )

    print(
        "Nenhum comando PJL arbitrário é aceito."
    )

    print(
        "Nenhum RESET automático será executado."
    )

    print(
        "Nenhum DEFAULT será executado."
    )

    print(
        "Nenhum JOB será enviado."
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

    print(
        f"RAW:        {RAW_PORT}"
    )

    print()

    print(
        "AÇÕES DISPONÍVEIS:"
    )

    print(
        "  query.status"
    )

    print(
        "  query.variables"
    )

    print(
        "  query.config"
    )

    print(
        "  paper.set"
    )

    print(
        "  mediatype.set"
    )

    print(
        "  duplex.set"
    )

    print(
        "  copies.set"
    )

    print(
        "  resolution.set"
    )

    print(
        "  density.set"
    )

    print(
        "  orientation.set"
    )

    print()

    action_name = input(
        "Digite a ação: "
    ).strip()

    value: Optional[str] = None

    if action_name.endswith(".set"):

        value = input(
            "Digite o valor: "
        ).strip()

    executor = ActionExecutor(
        ip=ip
    )

    result = executor.execute(
        action_name=action_name,
        value=value,
        confirm=True,
    )

    print()

    print("=" * 72)
    print("RESULTADO")
    print("=" * 72)

    if result.success:

        print()

        print(
            "✓ AÇÃO EXECUTADA."
        )

        print(
            f"Tempo: {result.elapsed:.3f}s"
        )

    else:

        print()

        print(
            "✗ AÇÃO NÃO EXECUTADA."
        )

        if result.error:

            print(
                f"Motivo: {result.error}"
            )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()