from dataclasses import dataclass


@dataclass

class Intent:

    tool: str

    action: str

    confidence: float = 1.0

    arguments: dict | None = None