"""Public LaTeX renderer API.

LaTeX source files conventionally use the ``.tex`` extension.  The public
format name is nevertheless ``latex`` so it is not confused with a generic
TeX renderer.
"""

from .tex import render_tex

render_latex = render_tex

__all__ = ["render_latex"]
