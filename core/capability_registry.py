import json
from pathlib import Path
from datetime import datetime


class CapabilityRegistry:

    def __init__(self, printer_ip, root="data/capabilities"):
        self.printer_ip = printer_ip
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

        safe_ip = printer_ip.replace(".", "_")
        self.path = self.root / f"{safe_ip}.json"

        self.data = self._load()

    def _load(self):
        if self.path.exists():
            try:
                return json.loads(
                    self.path.read_text(
                        encoding="utf-8"
                    )
                )
            except Exception:
                pass

        return {
            "printer": {
                "ip": self.printer_ip
            },
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "capabilities": []
        }

    def save(self):
        self.data["updated"] = datetime.now().isoformat()

        self.path.write_text(
            json.dumps(
                self.data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    def register(
        self,
        name,
        category,
        source,
        command=None,
        endpoint=None,
        parameter=None,
        values=None,
        status="UNKNOWN",
        evidence=None,
        notes=None
    ):

        capability = {
            "name": name,
            "category": category,
            "source": source,
            "status": status
        }

        if command is not None:
            capability["command"] = command

        if endpoint is not None:
            capability["endpoint"] = endpoint

        if parameter is not None:
            capability["parameter"] = parameter

        if values is not None:
            capability["values"] = values

        if evidence is not None:
            capability["evidence"] = evidence

        if notes is not None:
            capability["notes"] = notes

        # Não duplicar a mesma capacidade.
        for existing in self.data["capabilities"]:

            if (
                existing.get("name") == name
                and existing.get("source") == source
                and existing.get("parameter") == parameter
                and existing.get("endpoint") == endpoint
            ):
                existing.update(capability)
                self.save()
                return existing

        self.data["capabilities"].append(capability)
        self.save()

        return capability

    def find(self, name):
        return [
            item
            for item in self.data["capabilities"]
            if item.get("name") == name
        ]

    def all(self):
        return self.data["capabilities"]

    def summary(self):

        capabilities = self.data["capabilities"]

        result = {}

        for item in capabilities:

            category = item.get(
                "category",
                "UNKNOWN"
            )

            result.setdefault(category, 0)
            result[category] += 1

        return result