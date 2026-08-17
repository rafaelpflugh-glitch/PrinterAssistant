from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Option:
    value: str
    text: str
    selected: bool = False


@dataclass
class Field:
    field_type: str
    name: Optional[str] = None
    field_id: Optional[str] = None
    value: Optional[str] = None
    text: Optional[str] = None
    options: list[Option] = field(default_factory=list)


@dataclass
class Form:
    page_url: str
    action: str
    method: str
    fields: list[Field] = field(default_factory=list)


@dataclass
class Page:
    url: str
    status: int
    bytes: int
    title: str = ""
    links: list[str] = field(default_factory=list)
    forms: list[Form] = field(default_factory=list)


@dataclass
class Command:
    command_id: str
    category: str
    description: str
    page_url: str
    action: str
    method: str
    field_name: str
    field_type: str
    current_value: Optional[str] = None
    options: dict[str, str] = field(default_factory=dict)