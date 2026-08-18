
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class PrinterIdentity:
    """
    Identidade persistente de uma impressora.

    REGRA FUNDAMENTAL:
        serial = identidade permanente da máquina
        ip     = localização atual da máquina

    O IP pode mudar sem criar uma nova impressora.
    """

    def __init__(self, serial: str, registry_root: Optional[str] = None):
        serial = str(serial).strip()

        if not serial:
            raise ValueError("Número de série não pode ser vazio.")

        self.serial = serial

        if registry_root:
            self.root = Path(registry_root)
        else:
            # C:\PrinterAssistant\printers
            self.root = (
                Path(__file__).resolve().parents[2]
                / "printers"
            )

        self.root.mkdir(
            parents=True,
            exist_ok=True
        )

        self.path = self.root / f"{self._safe_filename(serial)}.json"

    @staticmethod
    def _safe_filename(value: str) -> str:
        """
        Converte o serial em um nome de arquivo seguro.
        """
        invalid = '<>:"/\\|?*'

        result = "".join(
            "_" if char in invalid else char
            for char in value
        )

        return result.strip() or "unknown"

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> dict:
        """
        Carrega a identidade persistente.
        """
        if not self.exists():
            return self.create()

        try:
            return json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                f"Não foi possível carregar "
                f"a identidade {self.serial}: {exc}"
            ) from exc

    def create(
        self,
        model: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> dict:
        """
        Cria um novo registro de impressora.
        """

        now = self._now()

        data = {
            "schema": "printerassistant.printer.identity.v1",

            "identity": {
                "serial": self.serial
            },

            "device": {
                "model": model
            },

            "network": {
                "current_ip": ip,
                "last_seen": now
            },

            "supplies": {},

            "capabilities": {},

            "history": [
                {
                    "event": "discovered",
                    "timestamp": now,
                    "ip": ip
                }
            ]
        }

        self.save(data)

        return data

    def save(self, data: dict) -> None:
        """
        Salva o registro da impressora.
        """

        self.path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    def update(
        self,
        ip: Optional[str] = None,
        model: Optional[str] = None,
        supplies: Optional[dict] = None,
        capabilities: Optional[dict] = None,
    ) -> dict:
        """
        Atualiza informações da máquina sem alterar sua identidade.

        O serial nunca é substituído.
        """

        data = self.load()

        now = self._now()

        if model:
            data.setdefault(
                "device",
                {}
            )["model"] = model

        if ip:
            network = data.setdefault(
                "network",
                {}
            )

            old_ip = network.get(
                "current_ip"
            )

            network["current_ip"] = ip
            network["last_seen"] = now

            # Registra mudança de IP.
            if old_ip and old_ip != ip:

                data.setdefault(
                    "history",
                    []
                ).append(
                    {
                        "event": "ip_changed",
                        "timestamp": now,
                        "old_ip": old_ip,
                        "new_ip": ip
                    }
                )

            elif not old_ip:

                data.setdefault(
                    "history",
                    []
                ).append(
                    {
                        "event": "ip_assigned",
                        "timestamp": now,
                        "ip": ip
                    }
                )

        if supplies is not None:
            data["supplies"] = supplies

        if capabilities is not None:
            data["capabilities"] = capabilities

        self.save(data)

        return data

    def register_discovery(
        self,
        ip: str,
        model: Optional[str] = None,
        supplies: Optional[dict] = None,
        capabilities: Optional[dict] = None,
    ) -> dict:
        """
        Registra uma descoberta.

        Se a impressora já existir:
            atualiza IP/modelo/etc.

        Se não existir:
            cria o registro.

        A decisão de identidade é SEMPRE o serial.
        """

        if self.exists():

            return self.update(
                ip=ip,
                model=model,
                supplies=supplies,
                capabilities=capabilities
            )

        return self.create(
            model=model,
            ip=ip
        )

    def summary(self) -> dict:
        """
        Retorna um resumo da identidade.
        """

        data = self.load()

        return {
            "serial": data.get(
                "identity",
                {}
            ).get(
                "serial"
            ),

            "model": data.get(
                "device",
                {}
            ).get(
                "model"
            ),

            "current_ip": data.get(
                "network",
                {}
            ).get(
                "current_ip"
            ),

            "last_seen": data.get(
                "network",
                {}
            ).get(
                "last_seen"
            ),

            "file": str(
                self.path
            )
        }


def find_printer_by_serial(
    serial: str,
    registry_root: Optional[str] = None
) -> Optional[PrinterIdentity]:
    """
    Procura uma impressora pelo número de série.
    """

    identity = PrinterIdentity(
        serial,
        registry_root=registry_root
    )

    if identity.exists():
        return identity

    return None


def list_printers(
    registry_root: Optional[str] = None
) -> list[dict]:
    """
    Lista todas as impressoras conhecidas.
    """

    if registry_root:
        root = Path(registry_root)
    else:
        root = (
            Path(__file__).resolve().parents[2]
            / "printers"
        )

    if not root.exists():
        return []

    printers = []

    for path in sorted(
        root.glob("*.json")
    ):

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            identity = data.get(
                "identity",
                {}
            )

            network = data.get(
                "network",
                {}
            )

            device = data.get(
                "device",
                {}
            )

            printers.append(
                {
                    "serial": identity.get(
                        "serial"
                    ),
                    "model": device.get(
                        "model"
                    ),
                    "current_ip": network.get(
                        "current_ip"
                    ),
                    "last_seen": network.get(
                        "last_seen"
                    ),
                    "file": str(path)
                }
            )

        except (
            json.JSONDecodeError,
            OSError
        ):
            continue

    return printers


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PrinterAssistant - "
            "Printer Identity Registry"
        )
    )

    parser.add_argument(
        "--serial",
        help="Número de série da impressora"
    )

    parser.add_argument(
        "--ip",
        help="IP atual da impressora"
    )

    parser.add_argument(
        "--model",
        help="Modelo da impressora"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista impressoras conhecidas"
    )

    args = parser.parse_args()

    if args.list:

        printers = list_printers()

        print()
        print("=" * 70)
        print("PRINTER ASSISTANT - PRINTER IDENTITY")
        print("=" * 70)
        print()

        if not printers:
            print("Nenhuma impressora registrada.")
        else:
            for printer in printers:
                print(
                    f"SERIAL : {printer['serial']}"
                )
                print(
                    f"MODEL  : {printer['model']}"
                )
                print(
                    f"IP     : {printer['current_ip']}"
                )
                print(
                    f"SEEN   : {printer['last_seen']}"
                )
                print(
                    f"FILE   : {printer['file']}"
                )
                print("-" * 70)

        raise SystemExit(0)

    if not args.serial:

        print(
            "ERRO: informe --serial "
            "ou use --list."
        )

        raise SystemExit(1)

    identity = PrinterIdentity(
        args.serial
    )

    identity.register_discovery(
        ip=args.ip,
        model=args.model
    )

    print()
    print("=" * 70)
    print("PRINTER ASSISTANT - IDENTITY")
    print("=" * 70)
    print()

    summary = identity.summary()

    print(
        f"Serial      : {summary['serial']}"
    )
    print(
        f"Modelo      : {summary['model']}"
    )
    print(
        f"IP atual    : {summary['current_ip']}"
    )
    print(
        f"Último scan : {summary['last_seen']}"
    )
    print(
        f"Arquivo     : {summary['file']}"
    )

    print()
    print("=" * 70)

