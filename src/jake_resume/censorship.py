from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from .model import Diagnostic


class CensorshipError(ValueError):
    """Raised when a censorship file is malformed."""


def _validate_path(path: Any, index: int) -> str:
    if not isinstance(path, str) or not path.strip():
        raise CensorshipError(f"censorship.remove[{index}] must be a non-empty string.")
    if path != path.strip() or "*" in path or "?" in path:
        raise CensorshipError(f"censorship.remove[{index}] must be an exact dotted path: {path!r}.")
    if any(part == "" for part in path.split(".")):
        raise CensorshipError(f"censorship.remove[{index}] contains an empty path component: {path!r}.")
    return path


def load_censorship_file(path: str | Path) -> list[str]:
    """Load and validate exact dotted paths from a censorship JSON file."""

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CensorshipError(f"Invalid censorship JSON in {path}: {exc.msg}.") from exc
    except UnicodeDecodeError as exc:
        raise CensorshipError(f"Invalid censorship text in {path}: {exc.reason}.") from exc

    if not isinstance(value, Mapping):
        raise CensorshipError("Censorship file must contain a JSON object.")
    paths = value.get("remove")
    if not isinstance(paths, list):
        raise CensorshipError("Censorship file must contain a 'remove' array.")
    return [_validate_path(item, index) for index, item in enumerate(paths)]


def _child(value: Any, component: str) -> tuple[bool, Any]:
    if isinstance(value, Mapping):
        if component in value:
            return True, value[component]
        return False, None
    if isinstance(value, list) and component.isdigit():
        index = int(component)
        if 0 <= index < len(value):
            return True, value[index]
    return False, None


def _remove_path(root: dict[str, Any], path: str) -> bool:
    components = path.split(".")
    parent: Any = root
    for component in components[:-1]:
        found, parent = _child(parent, component)
        if not found:
            return False

    final = components[-1]
    if isinstance(parent, Mapping):
        if final not in parent:
            return False
        del parent[final]
        return True
    if isinstance(parent, list) and final.isdigit():
        index = int(final)
        if 0 <= index < len(parent):
            del parent[index]
            return True
    return False


def apply_censorship(data: Mapping[str, Any], paths: Sequence[str]) -> tuple[dict[str, Any], list[Diagnostic]]:
    """Return a censored copy and warnings for paths that were not found."""

    if not isinstance(data, Mapping):
        raise CensorshipError("Resume input must be a JSON object before censorship can be applied.")

    censored = deepcopy(dict(data))
    diagnostics: list[Diagnostic] = []
    for index, path in enumerate(paths):
        if not _remove_path(censored, path):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    f"censorship.remove[{index}]",
                    f"Censorship path was not found: {path}",
                )
            )
    return censored, diagnostics
