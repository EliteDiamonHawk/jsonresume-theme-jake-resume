from __future__ import annotations

from collections.abc import Mapping
from html.parser import HTMLParser
import re
from typing import Any

from .model import Diagnostic, NormalizedResume, Section


TEX_ESCAPE = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

MONTHS = {
    "january": "Jan.",
    "february": "Feb.",
    "march": "Mar.",
    "april": "Apr.",
    "may": "May",
    "june": "Jun.",
    "july": "Jul.",
    "august": "Aug.",
    "september": "Sep.",
    "october": "Oct.",
    "november": "Nov.",
    "december": "Dec.",
}

IMPLEMENTATION_KEYS = frozenset({"id", "icon", "iconColor", "inlineLink"})
TITLE_KEYS = ("title", "name", "position", "role", "company", "organization", "institution", "school", "language")
DATE_KEYS = (
    "period",
    "dates",
    "dateRange",
    "date",
    "dateText",
    "startDate",
    "endDate",
    "startDateText",
    "endDateText",
)
LOCATION_KEYS = ("location", "city", "region", "country")
WEBSITE_KEYS = ("website", "url")
EXTRA_BULLET_KEYS = frozenset(
    {
        "description",
        "summary",
        "highlights",
        "bullets",
        "notes",
        "details",
        "responsibilities",
        "achievements",
        "duties",
        "content",
    }
)


def escape_text(value: Any) -> str:
    return "".join(TEX_ESCAPE.get(char, char) for char in str(value))


def normalize_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://", "mailto:", "tel:")):
        return text
    return "https://" + text


def escape_url(value: Any) -> str:
    """Escape a URL for a hyperref argument while preserving URL underscores."""

    text = str(value or "")
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
    )


def _label(key: str) -> str:
    if key == "value":
        return ""
    text = str(key).replace("_", " ").replace("-", " ")
    result: list[str] = []
    for char in text:
        if result and char.isupper() and result[-1][-1].islower():
            result.append(" ")
        result.append(char)
    text = "".join(result).strip()
    return text[:1].upper() + text[1:] if text else "Field"


class _RichTextParser(HTMLParser):
    """Convert the small HTML subset used by JSON Resume descriptions to LaTeX."""

    def __init__(self, diagnostics: list[Diagnostic], path: str) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.list_items: list[str] = []
        self.current_item: list[str] | None = None
        self.stack: list[str] = []
        self.diagnostics = diagnostics
        self.path = path
        self.warned: set[str] = set()

    def _target(self) -> list[str]:
        return self.current_item if self.current_item is not None else self.parts

    def _warn(self, tag: str) -> None:
        if tag not in self.warned:
            self.warned.add(tag)
            self.diagnostics.append(Diagnostic("warning", self.path, f"HTML tag <{tag}> was treated as plain content."))

    def handle_data(self, data: str) -> None:
        self._target().append(escape_text(data))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        target = self._target()
        if tag in {"strong", "b"}:
            target.append(r"\textbf{")
            self.stack.append("bold")
        elif tag in {"em", "i"}:
            target.append(r"\emph{")
            self.stack.append("italic")
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            if href:
                target.append(r"\resumeLink{" + escape_url(normalize_url(href)) + "}{")
                self.stack.append("link")
            else:
                self.stack.append("plain")
        elif tag in {"p", "div"}:
            if target and not target[-1].endswith("\n"):
                target.append("\n")
        elif tag == "br":
            target.append(r"\\ ")
        elif tag in {"ul", "ol"}:
            return
        elif tag == "li":
            if self.current_item is not None:
                self.list_items.append("".join(self.current_item).strip())
            self.current_item = []
        elif tag == "span":
            return
        else:
            self._warn(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        target = self._target()
        if tag in {"strong", "b", "em", "i", "a"}:
            if self.stack:
                kind = self.stack.pop()
                if kind in {"bold", "italic", "link"}:
                    target.append("}")
        elif tag == "li":
            if self.current_item is not None:
                self.list_items.append("".join(self.current_item).strip())
                self.current_item = None
        elif tag in {"p", "div"}:
            target.append("\n")

    def finish(self) -> tuple[str, list[str]]:
        if self.current_item is not None:
            self.list_items.append("".join(self.current_item).strip())
            self.current_item = None
        return "".join(self.parts).strip(), [item for item in self.list_items if item]


def _parse_rich_text(value: Any, diagnostics: list[Diagnostic], path: str) -> tuple[str, list[str]]:
    text = str(value or "")
    if "<" not in text or ">" not in text:
        return escape_text(text), []
    parser = _RichTextParser(diagnostics, path)
    try:
        parser.feed(text)
        parser.close()
        return parser.finish()
    except Exception as exc:  # pragma: no cover - defensive parser fallback
        diagnostics.append(Diagnostic("warning", path, f"Rich text could not be parsed: {exc}"))
        return escape_text(text), []


def rich_text(value: Any, diagnostics: list[Diagnostic], path: str) -> str:
    inline, _ = _parse_rich_text(value, diagnostics, path)
    return inline


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _is_implementation_key(key: str) -> bool:
    return key in IMPLEMENTATION_KEYS


def _mapping_text(value: Mapping[str, Any]) -> str:
    values: list[str] = []
    for key, item in value.items():
        if _is_implementation_key(str(key)) or _is_empty(item):
            continue
        values.append(str(item))
    return ", ".join(values)


def _format_date_atom(value: Any) -> str:
    if value is None or value == "":
        return ""
    text = str(value).strip()
    for month, short in MONTHS.items():
        text = re.sub(rf"\b{month}\b", short, text, flags=re.IGNORECASE)
    short_months = list(MONTHS.values())
    text = re.sub(
        r"(?<!\d)(\d{4})-(0[1-9]|1[0-2])(?!-\d)",
        lambda match: f"{short_months[int(match.group(2)) - 1]} {match.group(1)}",
        text,
    )
    text = re.sub(r"\s+[\-–—]\s+", " -- ", text)
    return text


def _date_range_text(value: Any) -> str:
    if isinstance(value, Mapping):
        start = next(
            (value.get(key) for key in ("start", "startDate", "startDateText", "from") if value.get(key) not in (None, "")),
            None,
        )
        end = next(
            (value.get(key) for key in ("end", "endDate", "endDateText", "to") if value.get(key) not in (None, "")),
            None,
        )
        if value.get("present") is True:
            end = "Present"
        if start and end:
            return f"{_format_date_atom(start)} -- {_format_date_atom(end)}"
        return _format_date_atom(start or end or "")
    if isinstance(value, list):
        return " -- ".join(_format_date_atom(item) for item in value if not _is_empty(item))
    return _format_date_atom(value)


def _date_value(value: Any, diagnostics: list[Diagnostic], path: str) -> str:
    return rich_text(_date_range_text(value), diagnostics, path)


def _date_for(item: Mapping[str, Any], diagnostics: list[Diagnostic], path: str) -> str:
    for key in DATE_KEYS:
        value = item.get(key)
        if not _is_empty(value):
            return _date_value(value, diagnostics, f"{path}.{key}")
    start = item.get("start")
    end = item.get("end")
    if start or end or item.get("present") is True:
        return _date_value({"start": start, "end": end, "present": item.get("present") is True}, diagnostics, path)
    return ""


def _location_for(item: Mapping[str, Any], diagnostics: list[Diagnostic], path: str) -> str:
    value = item.get("location")
    if isinstance(value, Mapping):
        return rich_text(_mapping_text(value), diagnostics, f"{path}.location")
    if value:
        return rich_text(value, diagnostics, f"{path}.location")
    parts = [item.get(key) for key in ("city", "region", "country") if item.get(key)]
    return rich_text(", ".join(str(part) for part in parts), diagnostics, f"{path}.location")


def _website_for(item: Mapping[str, Any], section_key: str, diagnostics: list[Diagnostic], path: str) -> str:
    raw = item.get("website")
    if raw is None:
        raw = item.get("url")
    if isinstance(raw, Mapping):
        url = raw.get("url")
        label = raw.get("label")
    else:
        url = raw
        label = None
    if not url:
        return ""
    label = str(label or "").strip()
    if not label or label == str(url).strip():
        label = "Credential" if section_key.lower() in {"certifications", "certificates"} else "Website"
    return rf"\resumeLink{{{escape_url(normalize_url(url))}}}{{{escape_text(label)}}}"


def _title_for(item: Mapping[str, Any], section_key: str) -> tuple[str, str | None]:
    if section_key.lower() in {"volunteer", "activities"}:
        for key in ("title", "name", "position", "role"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip(), key
        return "Member", None
    for key in TITLE_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip(), key
    return "", None


def _subtitle_for(item: Mapping[str, Any], title_key: str | None, section_key: str, diagnostics: list[Diagnostic], path: str) -> str:
    key = section_key.lower()
    parts: list[str] = []
    if key in {"volunteer", "activities"}:
        organization = item.get("organization") or item.get("company")
        if organization:
            parts.append(rich_text(organization, diagnostics, f"{path}.organization"))
    elif title_key in {"school", "institution"}:
        degree = item.get("degree")
        area = item.get("area") or item.get("field")
        if degree:
            parts.append(rich_text(degree, diagnostics, f"{path}.degree"))
        if area:
            parts.append(rich_text(f"in {area}" if degree else area, diagnostics, f"{path}.area"))
    else:
        organization = item.get("company") or item.get("organization") or item.get("employer") or item.get("issuer")
        if organization and str(organization) != str(item.get(title_key or "", "")):
            parts.append(rich_text(organization, diagnostics, f"{path}.organization"))
        explicit = item.get("subtitle")
        if explicit:
            parts.append(rich_text(explicit, diagnostics, f"{path}.subtitle"))
    website = _website_for(item, section_key, diagnostics, path)
    if website and key in {"certifications", "certificates"}:
        parts.append(rf"$|$ {website}")
    elif website and not parts:
        parts.append(website)
    return " ".join(part for part in parts if part)


def _bullet_values(value: Any, diagnostics: list[Diagnostic], path: str) -> list[str]:
    if isinstance(value, str):
        inline, items = _parse_rich_text(value, diagnostics, path)
        return items or ([inline] if inline else [])
    if isinstance(value, list):
        result: list[str] = []
        for index, item in enumerate(value):
            if _is_empty(item):
                continue
            result.extend(_bullet_values(item, diagnostics, f"{path}[{index}]"))
        return result
    if isinstance(value, Mapping):
        result = []
        for key, item in value.items():
            if _is_implementation_key(str(key)) or _is_empty(item):
                continue
            rendered = rich_text(item, diagnostics, f"{path}.{key}") if not isinstance(item, (Mapping, list)) else _mapping_text(item)
            if rendered:
                result.append(rf"\textbf{{{escape_text(_label(str(key)))}}}: {rendered}")
        return result
    text = rich_text(value, diagnostics, path)
    return [text] if text else []


def _render_extra_fields(item: Mapping[str, Any], title_key: str | None, section_key: str, diagnostics: list[Diagnostic], path: str) -> list[str]:
    consumed = set(TITLE_KEYS) | set(DATE_KEYS) | set(LOCATION_KEYS) | set(WEBSITE_KEYS) | {
        "hidden",
        "start",
        "end",
        "present",
        "subtitle",
        "field",
        "degree",
        "area",
        "company",
        "organization",
        "employer",
        "issuer",
    }
    result: list[str] = []
    for key, value in item.items():
        key = str(key)
        if key == title_key or key in consumed or _is_implementation_key(key) or _is_empty(value):
            continue
        label = "GPA" if key == "grade" else _label(key)
        values = _bullet_values(value, diagnostics, f"{path}.{key}")
        for rendered in values:
            if not rendered:
                continue
            if key in EXTRA_BULLET_KEYS:
                result.append(rendered)
            elif key == "grade":
                # GPA/grade text is ordinary entry content in Jake's source;
                # only skill/category labels use bold inline labels.
                result.append(rendered)
            else:
                result.append(rf"\textbf{{{escape_text(label)}}}: {rendered}")
    return result


def _render_entry(item: Mapping[str, Any], section_key: str, diagnostics: list[Diagnostic], path: str) -> str:
    title, title_key = _title_for(item, section_key)
    subtitle = _subtitle_for(item, title_key, section_key, diagnostics, path)
    date = _date_for(item, diagnostics, path)
    location = _location_for(item, diagnostics, path)
    extra = _render_extra_fields(item, title_key, section_key, diagnostics, path)
    lines: list[str] = []
    has_header = bool(title or subtitle or date or location)
    if has_header:
        title_tex = rich_text(title, diagnostics, path + "." + str(title_key)) if title else ""
        if subtitle or location:
            lines.append(rf"\resumeSubheading{{{title_tex}}}{{{date}}}{{{subtitle}}}{{{location}}}")
        else:
            lines.append(rf"\resumeSingleLine{{{title_tex}}}{{{date}}}")
    if extra and has_header:
        lines.append(r"\resumeItemListStart")
        lines.extend(rf"\resumeItem{{{value}}}" for value in extra)
        lines.append(r"\resumeItemListEnd")
    elif extra:
        lines.extend(rf"\resumeItem{{{value}}}" for value in extra)
    if not lines:
        lines.append(r"\resumeTextItem{}")
    return "\n".join(lines)


def _render_skill_item(item: Mapping[str, Any], diagnostics: list[Diagnostic], path: str) -> str:
    name = item.get("name") or item.get("language") or item.get("title") or item.get("category") or ""
    values = item.get("keywords") or item.get("skills") or item.get("fluency") or item.get("proficiency") or item.get("value")
    if isinstance(values, list):
        value = ", ".join(rich_text(value, diagnostics, f"{path}.keywords") for value in values if not _is_empty(value))
    elif isinstance(values, Mapping):
        value = _mapping_text(values)
    else:
        value = rich_text(values, diagnostics, f"{path}.value") if values else ""
    if item.get("language") and item.get("fluency") and item.get("keywords") is None:
        value = rich_text(item.get("fluency"), diagnostics, f"{path}.fluency")
    if not value:
        value = ", ".join(
            rich_text(item[key], diagnostics, f"{path}.{key}")
            for key in ("description", "summary")
            if item.get(key)
        )
    return rf"\resumeSkill{{{rich_text(name, diagnostics, path + '.name')}}}{{{value}}}"


def _render_summary(section: Section, diagnostics: list[Diagnostic]) -> str:
    values: list[str] = []
    for index, item in enumerate(section.items):
        for key, value in item.items():
            if _is_implementation_key(str(key)) or _is_empty(value):
                continue
            values.extend(_bullet_values(value, diagnostics, f"sections.{section.key}[{index}].{key}"))
    if not values:
        return ""
    return "\n".join(
        [
            rf"\resumeSection{{{escape_text(section.title)}}}",
            rf"\resumeTextBlock{{{' '.join(values)}}}",
        ]
    )


def _render_section(section: Section, diagnostics: list[Diagnostic]) -> str:
    key = section.key.lower()
    if key == "profiles" or section.hidden or not section.items:
        return ""
    if key == "summary":
        return _render_summary(section, diagnostics)
    if key in {"skills", "languages", "interests"}:
        body = [rf"\resumeSection{{{escape_text(section.title)}}}", r"\resumeSkillListStart", r"\small{\item{"]
        for index, item in enumerate(section.items):
            if item.get("hidden") is not True:
                body.append(_render_skill_item(item, diagnostics, f"sections.{section.key}[{index}]"))
        body.extend([r"}}", r"\resumeSkillListEnd"])
        return "\n".join(body)
    body = [rf"\resumeSection{{{escape_text(section.title)}}}", r"\resumeSubHeadingListStart"]
    for index, item in enumerate(section.items):
        if item.get("hidden") is not True:
            body.append(_render_entry(item, section.key, diagnostics, f"sections.{section.key}[{index}]"))
    body.append(r"\resumeSubHeadingListEnd")
    return "\n".join(body)


def _profile_link(profile: Mapping[str, Any], diagnostics: list[Diagnostic], path: str) -> tuple[str, str] | None:
    if profile.get("hidden") is True:
        return None
    website = profile.get("website")
    if isinstance(website, Mapping):
        url = website.get("url")
        website_label = website.get("label")
    else:
        url = website or profile.get("url")
        website_label = None
    if not url:
        return None
    label = profile.get("network") or website_label or profile.get("username") or url
    return normalize_url(url), rich_text(label, diagnostics, f"{path}.website.label")


def _profile_links(resume: NormalizedResume, diagnostics: list[Diagnostic]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    candidates: list[tuple[Mapping[str, Any], str]] = []
    basics_profiles = resume.basics.get("profiles")
    if isinstance(basics_profiles, list):
        candidates.extend(
            (profile, f"basics.profiles[{index}]")
            for index, profile in enumerate(basics_profiles)
            if isinstance(profile, Mapping)
        )
    for section in resume.sections:
        if section.key.lower() == "profiles":
            candidates.extend(
                (profile, f"sections.{section.key}[{index}]")
                for index, profile in enumerate(section.items)
                if isinstance(profile, Mapping)
            )
    for profile, path in candidates:
        link = _profile_link(profile, diagnostics, path)
        if link is None:
            continue
        url, label = link
        if url in seen:
            continue
        seen.add(url)
        links.append(rf"\resumeLink{{{escape_url(url)}}}{{{label}}}")
    return links


def _header_location(value: Any, diagnostics: list[Diagnostic]) -> str:
    text = _mapping_text(value) if isinstance(value, Mapping) else str(value or "")
    text = re.sub(r",\s*(?:US|USA)$", "", text, flags=re.IGNORECASE)
    return rich_text(text, diagnostics, "basics.location")


def _header(resume: NormalizedResume, diagnostics: list[Diagnostic]) -> str:
    basics = resume.basics
    name = basics.get("name") or basics.get("fullName") or "Resume"
    contacts: list[str] = []
    if basics.get("location"):
        contacts.append(_header_location(basics["location"], diagnostics))
    if basics.get("phone"):
        phone = basics["phone"]
        contacts.append(rf"\resumeLink{{tel:{escape_url(phone)}}}{{{escape_text(phone)}}}")
    if basics.get("email"):
        email = basics["email"]
        contacts.append(rf"\resumeLink{{mailto:{escape_url(email)}}}{{{escape_text(email)}}}")
    website = basics.get("website") or basics.get("url")
    if isinstance(website, Mapping):
        website_url = website.get("url")
        website_label = website.get("label") or "Portfolio"
    else:
        website_url = website
        website_label = basics.get("urlLabel") or "Portfolio"
    if website_url:
        contacts.append(rf"\resumeLink{{{escape_url(normalize_url(website_url))}}}{{{escape_text(website_label)}}}")
    contacts.extend(_profile_links(resume, diagnostics))
    headline = basics.get("label") or basics.get("headline")
    lines = [r"\begin{center}", rf"    \textbf{{\Huge \scshape {escape_text(name)}}} \\ \vspace{{5pt}}"]
    if headline:
        lines.append(rf"    \small {rich_text(headline, diagnostics, 'basics.headline')} \\")
    if contacts:
        lines.append("    " + r"\small " + r" $|$ ".join(contacts) + r" \\")
    lines.append(r"\end{center}")
    return "\n".join(lines)


def _document_preamble() -> list[str]:
    return [
        r"\documentclass[letterpaper,11pt]{article}",
        r"\usepackage{latexsym}",
        r"\usepackage[empty]{fullpage}",
        r"\usepackage{titlesec}",
        r"\usepackage{marvosym}",
        r"\usepackage[usenames,dvipsnames]{color}",
        r"\usepackage{verbatim}",
        r"\usepackage{enumitem}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\usepackage{fancyhdr}",
        r"\usepackage[english]{babel}",
        r"\usepackage{tabularx}",
        r"\input{glyphtounicode}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\fancyfoot{}",
        r"\renewcommand{\headrulewidth}{0pt}",
        r"\renewcommand{\footrulewidth}{0pt}",
        r"\addtolength{\oddsidemargin}{-0.5in}",
        r"\addtolength{\evensidemargin}{-0.5in}",
        r"\addtolength{\textwidth}{1in}",
        r"\addtolength{\topmargin}{-.5in}",
        r"\addtolength{\textheight}{1.0in}",
        r"\urlstyle{same}",
        r"\raggedbottom",
        r"\raggedright",
        r"\setlength{\tabcolsep}{0in}",
        r"\titleformat{\section}{\vspace{-4pt}\scshape\raggedright\large}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]",
        r"\pdfgentounicode=1",
    ]


def render_tex(resume: NormalizedResume) -> str:
    diagnostics = resume.diagnostics
    sections = [_render_section(section, diagnostics) for section in resume.sections]
    sections = [section for section in sections if section]
    return "\n".join(
        [
            r"% Generated by jake-resume; edit the JSON input instead of this file.",
            *_document_preamble(),
            r"\newcommand{\resumeLink}[2]{\underline{\href{#1}{#2}}}",
            r"\newcommand{\resumeSection}[1]{\section{#1}}",
            r"\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}",
            r"\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}",
            r"\newcommand{\resumeItemListStart}{\begin{itemize}}",
            r"\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}",
            r"\newcommand{\resumeItem}[1]{\item\small{{#1 \vspace{-2pt}}}}",
            r"\newcommand{\resumeSubheading}[4]{\vspace{-2pt}\item\begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}\textbf{#1} & #2 \\\textit{\small#3} & \textit{\small #4} \\\end{tabular*}\vspace{-7pt}}",
            r"\newcommand{\resumeSubSubheading}[2]{\item\begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}\textit{\small#1} & \textit{\small #2} \\\end{tabular*}\vspace{-7pt}}",
            r"\newcommand{\resumeProjectHeading}[2]{\item\begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}\small#1 & #2 \\\end{tabular*}\vspace{-7pt}}",
            r"\newcommand{\resumeSingleLine}[2]{\resumeProjectHeading{\textbf{#1}}{#2}}",
            r"\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}",
            r"\newcommand{\resumeTextItem}[1]{\resumeItem{#1}}",
            r"\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}",
            r"\newcommand{\resumeSkillListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}",
            r"\newcommand{\resumeSkillListEnd}{\end{itemize}}",
            r"\newcommand{\resumeSkill}[2]{\textbf{#1}{: #2} \\}",
            r"\newcommand{\resumeTextBlock}[1]{\small{#1\par}\vspace{-2pt}}",
            r"\begin{document}",
            _header(resume, diagnostics),
            "\n".join(sections),
            r"\end{document}",
            "",
        ]
    )
