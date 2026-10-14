"""Python API for the schema-driven Jake-style resume renderer."""

from .adapters import detect_format, normalize
from .model import Diagnostic, NormalizedResume, Section
from .render import compile_pdf, render_html, render_latex, render_svg, render_tex

__all__ = [
    "Diagnostic",
    "NormalizedResume",
    "Section",
    "compile_pdf",
    "detect_format",
    "normalize",
    "render_html",
    "render_latex",
    "render_svg",
    "render_tex",
]
