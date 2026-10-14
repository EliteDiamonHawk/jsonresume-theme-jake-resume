from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DiagnosticLevel = Literal["warning", "error"]


@dataclass(frozen=True)
class Diagnostic:
    level: DiagnosticLevel
    path: str
    message: str

    def __str__(self) -> str:
        location = f" at {self.path}" if self.path else ""
        return f"{self.level}: {self.message}{location}"


@dataclass
class Section:
    key: str
    title: str
    items: list[dict[str, Any]] = field(default_factory=list)
    hidden: bool = False
    source: str = ""


@dataclass
class NormalizedResume:
    format: str
    basics: dict[str, Any] = field(default_factory=dict)
    summary: Any = None
    sections: list[Section] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    picture: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def warnings(self) -> list[Diagnostic]:
        return [item for item in self.diagnostics if item.level == "warning"]

    @property
    def errors(self) -> list[Diagnostic]:
        return [item for item in self.diagnostics if item.level == "error"]
