from dataclasses import dataclass, field


@dataclass(slots=True)
class Intent:

    tool: str

    action: str

    confidence: float = 1.0

    arguments: dict = field(default_factory=dict)

    text: str = ""

    source: str = "resolver"

    def __repr__(self):

        return (

            f"Intent("

            f"tool={self.tool!r}, "

            f"action={self.action!r}, "

            f"confidence={self.confidence}, "

            f"arguments={self.arguments}"

            f")"

        )