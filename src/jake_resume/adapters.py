from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .model import Diagnostic, NormalizedResume, Section


class InputError(ValueError):
    """Raised when input cannot be normalized into a resume document."""


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _humanize(key: str) -> str:
    text = str(key).replace("_", " ").replace("-", " ")
    result: list[str] = []
    for char in text:
        if result and char.isupper() and result[-1][-1].islower():
            result.append(" ")
        result.append(char)
    text = "".join(result).strip()
    return text[:1].upper() + text[1:] if text else "Section"


def _section_items(value: Any, path: str, diagnostics: list[Diagnostic]) -> list[dict[str, Any]]:
    if isinstance(value, list):
        items: list[dict[str, Any]] = []
        for index, item in enumerate(value):
            if isinstance(item, Mapping):
                items.append(deepcopy(dict(item)))
            elif item is not None:
                items.append({"value": deepcopy(item)})
            else:
                diagnostics.append(Diagnostic("warning", f"{path}[{index}]", "Null section item was ignored."))
        return items
    if isinstance(value, Mapping):
        return [deepcopy(dict(value))]
    if value is None:
        return []
    return [{"value": deepcopy(value)}]


def detect_format(data: Mapping[str, Any]) -> str:
    if not isinstance(data, Mapping):
        raise InputError("Resume input must be a JSON object.")
    if isinstance(data.get("sections"), Mapping) and (
        "metadata" in data or "customSections" in data or "picture" in data
    ):
        return "rxresume-v5"
    return "jsonresume"


def _jsonresume(data: Mapping[str, Any]) -> NormalizedResume:
    diagnostics: list[Diagnostic] = []
    basics = _mapping(data.get("basics"))
    metadata = _mapping(data.get("meta"))
    aliases = _mapping(metadata.get("aliases"))
    sections: list[Section] = []
    ignored = {"basics", "meta", "$schema", "version"}

    for key, value in data.items():
        if key in ignored:
            continue
        if isinstance(value, (list, Mapping)) or value is not None:
            alias = aliases.get(key)
            title = alias.strip() if isinstance(alias, str) and alias.strip() else _humanize(key)
            sections.append(
                Section(
                    key=str(key),
                    title=title,
                    items=_section_items(value, str(key), diagnostics),
                    source="jsonresume",
                )
            )

    summary = basics.get("summary")
    return NormalizedResume(
        format="jsonresume",
        basics=basics,
        summary=summary,
        sections=sections,
        metadata=metadata,
        diagnostics=diagnostics,
    )


def _rx_section(key: str, value: Mapping[str, Any], source: str) -> Section:
    items = value.get("items")
    if not isinstance(items, list):
        items = []
    visible: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and item.get("hidden") is not True:
            visible.append(deepcopy(dict(item)))
    raw_title = value.get("title")
    title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else _humanize(key)
    return Section(key=key, title=title, items=visible, hidden=value.get("hidden") is True, source=source)


def _rx_order(section_map: dict[str, Section], metadata: Mapping[str, Any]) -> list[str]:
    ordered: list[str] = []
    layout = _mapping(metadata.get("layout"))
    pages = layout.get("pages")
    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, Mapping):
                continue
            for area in ("main", "sidebar"):
                values = page.get(area)
                if not isinstance(values, list):
                    continue
                for value in values:
                    key = str(value)
                    if key in section_map and key not in ordered:
                        ordered.append(key)
    ordered.extend(key for key in section_map if key not in ordered)
    return ordered


def _rxresume(data: Mapping[str, Any]) -> NormalizedResume:
    diagnostics: list[Diagnostic] = []
    basics = _mapping(data.get("basics"))
    summary = data.get("summary")
    if isinstance(summary, Mapping):
        summary = summary.get("content") or summary.get("description") or summary.get("text")

    sections_map: dict[str, Section] = {}
    raw_sections = data.get("sections")
    if isinstance(raw_sections, Mapping):
        for key, value in raw_sections.items():
            if isinstance(value, Mapping):
                section = _rx_section(str(key), value, "rxresume-v5")
                if not section.hidden:
                    sections_map[section.key] = section
            else:
                diagnostics.append(Diagnostic("warning", f"sections.{key}", "Section value is not an object and was ignored."))

    if isinstance(summary, str) and summary.strip():
        summary_value = data.get("summary")
        summary_title = "Summary"
        if isinstance(summary_value, Mapping) and isinstance(summary_value.get("title"), str) and summary_value.get("title"):
            summary_title = summary_value["title"]
        sections_map["summary"] = Section(
            key="summary",
            title=summary_title,
            items=[{"value": summary}],
            source="rxresume-v5",
        )

    custom = data.get("customSections")
    if isinstance(custom, list):
        for index, value in enumerate(custom):
            if not isinstance(value, Mapping) or value.get("hidden") is True:
                continue
            key = str(value.get("id") or f"custom-{index + 1}")
            sections_map[key] = _rx_section(key, value, "rxresume-v5")

    metadata = _mapping(data.get("metadata"))
    sections = [sections_map[key] for key in _rx_order(sections_map, metadata)]
    picture = _mapping(data.get("picture"))
    if picture and picture.get("hidden") is not True and picture.get("url"):
        diagnostics.append(
            Diagnostic(
                "warning",
                "picture",
                "Picture and QR styling are intentionally omitted from the Jake layout.",
            )
        )

    return NormalizedResume(
        format="rxresume-v5",
        basics=basics,
        summary=summary,
        sections=sections,
        metadata=metadata,
        picture=picture,
        diagnostics=diagnostics,
    )


def normalize(data: Mapping[str, Any], input_format: str = "auto") -> NormalizedResume:
    if not isinstance(data, Mapping):
        raise InputError("Resume input must be a JSON object.")
    selected = detect_format(data) if input_format == "auto" else input_format
    if selected == "jsonresume":
        return _jsonresume(data)
    if selected in {"rxresume", "rxresume-v5"}:
        return _rxresume(data)
    raise InputError(f"Unsupported input format: {input_format}")
